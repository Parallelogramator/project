from PyQt6 import QtWidgets

class FilterDialog(QtWidgets.QDialog):
    def __init__(self, headers):
        super().__init__()

        self.setWindowTitle("Filter Data")

        self.layout = QtWidgets.QVBoxLayout(self)

        # Создаем выпадающий список с заголовками
        self.header_list = QtWidgets.QComboBox()
        self.header_list.addItems(headers)
        self.layout.addWidget(self.header_list)

        # Создаем поле для ввода значения фильтра
        self.value_input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.value_input)

        # Создаем кнопки ОК и Отмена
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_values(self):
        # Возвращаем выбранный заголовок и введенное значение
        return self.header_list.currentText(), self.value_input.text()
