import sqlite3

from PyQt5.QtWidgets import QApplication,QPushButton,QMessageBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, \
    QListWidget, QListWidgetItem, QFileDialog, QGridLayout, QLineEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from urllib.request import urlopen
import sys
from PyQt5.QtGui import QMovie


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


           # 添加收藏列表和列表控件
        self.current_game_details = None  # 用于保存当前显示的游戏的详细信息

        self.favorites_list = []  # 用于存储收藏游戏的详细信息
        self.favorites_list_widget = QListWidget()  # 显示收藏游戏名称的列表控件
        self.favorites_list_widget.setSelectionMode(QListWidget.MultiSelection)  # 允许多选

        # 创建添加到收藏的按钮
        self.add_to_favorites_button = QPushButton("加入收藏列表")
        self.add_to_favorites_button.clicked.connect(self.add_to_favorites)
        self.add_to_favorites_button.setDisabled(True)  # 初始时禁用按钮，直到有游戏被选中

        # 添加删除按钮
        self.delete_from_favorites_button = QPushButton("删除")
        self.delete_from_favorites_button.clicked.connect(self.delete_from_favorites)
        self.delete_from_favorites_button.setDisabled(True)  # 初始时禁用按钮，直到有游戏被选中

        # 将收藏列表控件和按钮添加到布局中
        favorites_layout = QVBoxLayout()
        favorites_layout.addWidget(self.favorites_list_widget)
        favorites_layout.addWidget(self.add_to_favorites_button)
        favorites_layout.addWidget(self.delete_from_favorites_button)
        main_layout.addLayout(favorites_layout)  # 将收藏列表布局添加到主布局中

        # 初始化搜索框为不可编辑
        self.search_edit.setDisabled(True)

        self.game_content_image_widget = QLabel()

        self.selected_item = None




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
        self.game_content_image_widget.setMovie(QMovie("./assest/loading.gif"))
        self.game_content_image_widget.movie().start()
        # 获取所选游戏的标题
        selected_title = item.text()
        self.selected_item = selected_title
        # 连接到先前选择导入的SQLite数据库
        connection = sqlite3.connect(self.db_filename)
        cursor = connection.cursor()

        # 查询所选游戏的所有字段
        cursor.execute("SELECT * FROM games WHERE title=?", (selected_title,))
        game_data = cursor.fetchone()
        self.current_game_details = game_data  # 保存当前游戏的详细信息
        # 显示详情部分
        self.clear_layout(self.details_widget.layout())
        for i, (field, value) in enumerate(zip(cursor.description, game_data)):
            label = QLabel(f"{field[0]}:")
            self.details_widget.layout().addWidget(label, i, 0)

            if field[0] == "image_url":
                # 如果是图片URL，则显示图片
                self.details_widget.layout().addWidget(self.game_content_image_widget, i, 1)
                self.load_image(self.prepend_domain(value),i,selected_title)
                # pass
            elif field[0] == "url":
                # 如果是URL字段，则创建链接
                url_label = QLabel(f'<a href="{self.prepend_domain(value)}">{value}</a>')
                url_label.setOpenExternalLinks(True)
                self.details_widget.layout().addWidget(url_label, i, 1)
            else:
                # 否则显示文本值
                value_label = QLabel(str(value))
                self.details_widget.layout().addWidget(value_label, i, 1)
         # 游戏详情显示后，启用添加到收藏的按钮
        self.add_to_favorites_button.setDisabled(False)
        
        # 关闭数据库连接
        cursor.close()
        connection.close()
    
    def add_to_favorites(self):
        # 添加当前查看的游戏到收藏列表
        if self.selected_item and self.selected_item not in self.favorites_list:
            self.favorites_list.append(self.selected_item)
            self.favorites_list_widget.addItem(self.selected_item)
            self.delete_from_favorites_button.setDisabled(False)  # 有收藏项时启用删除按钮
        else:
            QMessageBox.information(self, "提示", "该游戏已存在于收藏列表中。")
    def delete_from_favorites(self):
        # 从收藏列表中删除选中的游戏
        selected_items = self.favorites_list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                self.favorites_list_widget.takeItem(self.favorites_list_widget.row(item))
                self.favorites_list.remove(item.text())
            if not self.favorites_list:
                self.delete_from_favorites_button.setDisabled(True)  # 无收藏项时禁用删除按钮   

    def prepend_domain(self, url):
        # 拼接域名并返回完整的URL
        return f"http://www.emumax.com{url}"

    def show_image(self, pixmap,i,name):
         if(name != self.selected_item):
             return
         self.game_content_image_widget.movie().stop()
         self.game_content_image_widget.setPixmap(pixmap)
         
         

    def load_image(self, url,i,name):
        # 创建加载图片的线程
        self.image_loading_thread = ImageLoadingThread(url,i,name)

        # 连接图片加载完成的信号到显示图片的槽函数
        self.image_loading_thread.image_loaded.connect(self.show_image)

        # 启动线程
        self.image_loading_thread.start()

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

class ImageLoadingThread(QThread):
    
    # 定义一个信号，用于在图片加载完成后通知主线程
    image_loaded = pyqtSignal(QPixmap,int,str)

    def __init__(self, url,i,name):
        super().__init__()
        self.url = url
        self.i = i
        self.name = name

    def run(self):
        # 在这个线程中加载图片
        data = urlopen(self.url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if pixmap.isNull():
            print("图片加载失败。")
            return
        
        # 图片加载完成后，发出信号
        self.image_loaded.emit(pixmap,self.i,self.name)

def main():
    app = QApplication(sys.argv)
    window = RomsBrowserApp()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
