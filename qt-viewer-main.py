import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QFileDialog, QGridLayout, QLineEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from urllib.request import urlopen
import sys

class RomsBrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置主窗口标题
        self.setWindowTitle("roms浏览器")

        # 数据库文件名称（默认为None，需要在运行时设置）
        self.db_filename = None

        # 创建主布局
        main_layout = QHBoxLayout()

        # 创建菜单栏
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("文件")
        import_action = file_menu.addAction("导入db")
        import_action.triggered.connect(self.import_db)
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        # 创建搜索框
        search_layout = QVBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索标题")
        self.search_edit.textChanged.connect(self.filter_list)
        search_layout.addWidget(self.search_edit)

        # 创建左侧列表部分
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.show_details)
        search_layout.addWidget(self.list_widget)

        # 创建右侧详情部分
        self.details_widget = QWidget()
        details_layout = QGridLayout(self.details_widget)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.details_widget)

        # 设置主窗口布局
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化搜索框为不可编辑
        self.search_edit.setDisabled(True)

    def import_db(self):
        # 打开文件对话框以选择要导入的SQLite文件
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "选择要导入的SQLite文件", "", "SQLite数据库文件 (*.db *.sqlite)")

        if file_path:
            # 设置数据库文件名称
            self.db_filename = file_path

            # 连接到SQLite数据库
            connection = sqlite3.connect(self.db_filename)
            cursor = connection.cursor()

            # 从数据库中读取数据
            cursor.execute("SELECT title FROM games")
            titles = cursor.fetchall()

            # 将数据填充到左侧列表部分
            self.list_widget.clear()
            for title in titles:
                item = QListWidgetItem(title[0])
                self.list_widget.addItem(item)

            # 关闭数据库连接
            cursor.close()
            connection.close()

            # 设置搜索框内容为空
            self.search_edit.clear()

            # 启用搜索框
            self.search_edit.setDisabled(False)

    def show_details(self, item):
        if not self.db_filename:
            print("请先导入数据库。")
            return

        # 获取所选游戏的标题
        selected_title = item.text()

        # 连接到先前选择导入的SQLite数据库
        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()

        # 查询所选游戏的所有字段
        cursor.execute("SELECT * FROM games WHERE title=?", (selected_title,))
        game_data = cursor.fetchone()

        # 显示详情部分
        self.clear_layout(self.details_widget.layout())
        for i, (field, value) in enumerate(zip(cursor.description, game_data)):
            label = QLabel(f"{field[0]}:")
            self.details_widget.layout().addWidget(label, i, 0)

            if field[0] == "image_url":
                # 如果是图片URL，则显示图片
                # pixmap = self.load_image(value)
                # image_label = QLabel()
                # image_label.setPixmap(pixmap)
                # self.details_widget.layout().addWidget(image_label, i, 1)
                pass
            elif field[0] == "url":
                # 如果是URL字段，则创建链接
                url_label = QLabel(f'<a href="{self.prepend_domain(value)}">{value}</a>')
                url_label.setOpenExternalLinks(True)
                self.details_widget.layout().addWidget(url_label, i, 1)
            else:
                # 否则显示文本值
                value_label = QLabel(str(value))
                self.details_widget.layout().addWidget(value_label, i, 1)

        # 关闭数据库连接
        cursor.close()
        connection.close()
    def prepend_domain(self, url):
        # 拼接域名并返回完整的URL
        return f"http://www.emumax.com{url}"

    def load_image(self, url):
        # 从URL加载图片并返回QPixmap
        response = urlopen(url)
        image_data = response.read()
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        return pixmap

    def clear_layout(self, layout):
        # 清除布局中的所有子部件
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                self.clear_layout(item.layout())

    def filter_list(self):
        if not self.db_filename:
            return

        # 获取搜索框中的文本
        filter_text = self.search_edit.text()

        # 清空列表
        self.list_widget.clear()

        # 连接到SQLite数据库
        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()

        # 查询符合搜索条件的游戏标题
        cursor.execute("SELECT title FROM games WHERE title LIKE ?", ('%' + filter_text + '%',))
        titles = cursor.fetchall()

        # 将数据填充到左侧列表部分
        for title in titles:
            item = QListWidgetItem(title[0])
            self.list_widget.addItem(item)

        # 关闭数据库连接
        cursor.close()
        connection.close()

def main():
    app = QApplication(sys.argv)
    window = RomsBrowserApp()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
