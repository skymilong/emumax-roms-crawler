# 被调用方，提供方法暴露给调用方。入参为文件夹路径，在这里根据路径打开文件夹，编辑文件夹内容
# 调用方：qt/main.py
# Path: qt/main.py
# Compare this snippet from qt/game_list_viewer.py:
#         self.game_list_viewer = GameListViewer()
#         self.setCentralWidget(self.game_list_viewer)
# 