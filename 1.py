import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
import os
from sql import Ui_Form as sql
from filter import FilterDialog

class ImageDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.label = QtWidgets.QLabel(self)

        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)

        self.label.setPixmap(pixmap)



class DbViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Подключаемся к базе данных SQLite
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(self.select_database())

        if not db.open():
            print(f"Cannot open database: {db.lastError().text()}")
            exit()


        self.db = db
        self.table_model = QSqlTableModel(db=self.db)

        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.table_model)

        self.tables = []
        self.next_index = 0

        query = QSqlQuery()
        query.exec('SELECT name FROM sqlite_master WHERE type="table"')
        while query.next():
            self.tables.append(query.value(0))

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Database Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.initialize_db()

        # Добавляем панель инструментов с кнопками "Добавить", "Обновить", "Фильтровать", "Переключить вид" и "сброс"
        toolbar = QtWidgets.QToolBar()
        self.addToolBar(toolbar)

        self.table_combo_box = QtWidgets.QComboBox()
        self.table_combo_box.addItems(self.tables)
        self.table_combo_box.currentIndexChanged.connect(self.update_table)
        toolbar.addWidget(self.table_combo_box)

        add_action = QtGui.QAction("Add", self)
        add_action.triggered.connect(self.add_user)
        toolbar.addAction(add_action)

        update_action = QtGui.QAction("Update", self)
        update_action.triggered.connect(self.update_user)
        toolbar.addAction(update_action)

        filter_action = QtGui.QAction("Filter", self)
        filter_action.triggered.connect(self.filter_data)
        toolbar.addAction(filter_action)


        execute_sql_action = QtGui.QAction("Execute SQL", self)
        execute_sql_action.triggered.connect(self.execute_sql)
        toolbar.addAction(execute_sql_action)

        reset_action = QtGui.QAction("Reset", self)
        reset_action.triggered.connect(self.reset_table)
        toolbar.addAction(reset_action)


        self.table_view.doubleClicked.connect(self.show_image)


    def select_database(self):
            options = QtWidgets.QFileDialog(self).options()
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                                "SQLite Files (*.db);;CSV Files (*.csv)",
                                                                options=options)
            if fileName:
                if fileName.endswith('.csv'):
                    try:
                        db = fileName[:-4]
                        import csv
                        import sqlite3

                        # Создайте соединение с новой базой данных SQLite
                        conn = sqlite3.connect(f'{db}.db')
                        cur = conn.cursor()
                        query = ''
                        # Откройте CSV-файл и прочитайте первую строку, чтобы получить имена столбцов
                        with open(fileName, 'r', encoding='utf-8') as csv_file:
                            csv_reader = csv.reader(csv_file, delimiter=';', quotechar='"')
                            column_names = next(csv_reader)
                            query = f"CREATE TABLE {db.split('/')[-1]} ( {', '.join([f'{name} TEXT' for name in column_names])})"
                            # Создайте строку SQL для создания таблицы
                            cur.execute(query)

                            # Вставьте данные из CSV-файла в таблицу
                            for row in csv_reader:
                                query = f"INSERT INTO {db.split('/')[-1]} VALUES ({', '.join(['?' for _ in column_names])})"
                                cur.execute(query, row)

                        # Сохраните изменения и закройте соединение
                        conn.commit()


                        return f'{db}.db'
                    except Exception as err:
                        error = ('Query Failed: %s\nError: %s' % (query, str(err)))
                        QtWidgets.QMessageBox.critical(self, "SQL",
                                                       error)
                    finally:
                        conn.close()
                else:
                    return fileName
            else:
                exit()



    def initialize_db(self):
        # Создаем объект QTableView
        self.table_view = QtWidgets.QTableView()

        # Отключаем прямое редактирование таблицы
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        # Устанавливаем table_view в качестве центрального виджета
        self.setCentralWidget(self.table_view)

        # Устанавливаем таблицу для модели
        self.table_model.setTable(self.tables[self.next_index])
        # Выполняем выборку данных
        self.table_model.select()
        # Устанавливаем модель для table_view
        self.table_view.setModel(self.proxy_model)

        # Включаем сортировку
        self.table_view.setSortingEnabled(True)
        # Сортируем данные по возрастанию в первом столбце
        self.proxy_model.sort(0, QtCore.Qt.SortOrder.AscendingOrder)


    def add_user(self):
        # Создаем список заголовков для диалогового окна
        dialog = [self.table_model.headerData(i, QtCore.Qt.Orientation.Horizontal) for i in
                  range(self.table_model.columnCount())]

        # Создаем список данных, начиная с номера следующей строки
        data = [self.table_model.rowCount() + 1]
        # Для каждого столбца в модели открываем диалоговое окно ввода и добавляем введенное значение в запись
        for i in range(1, self.table_model.columnCount()):
            input_dialog = QtWidgets.QInputDialog()
            input_dialog.setInputMode(QtWidgets.QInputDialog.InputMode.TextInput)
            input_dialog.setLabelText(dialog[i])
            ok = input_dialog.exec()
            if ok:
                value = input_dialog.textValue()
                data.append(value)
            else:
                return False

        # Создаем объект QSqlQuery
        query = QSqlQuery()

        # Подготавливаем запрос на вставку данных
        query.prepare(
            f'INSERT INTO {self.tables[self.next_index]} VALUES ({", ".join([":value" + str(i) for i in range(len(dialog))])})')
        # Привязываем значения к запросу
        for i, value in enumerate(data):
            query.bindValue(":value" + str(i), value)
        query.exec()
        # Переинициализируем базу данных
        self.initialize_db()

    def update_user(self):
        # Открываем диалоговое окно для ввода идентификатора пользователя
        id, ok = QtWidgets.QInputDialog.getInt(self, "Update User", "Enter id:")

        if ok and id != 0:

            # Ищем строку с данным идентификатором пользователя
            for row in range(self.proxy_model.rowCount()):
                index = self.proxy_model.index(row, 0)
                source_index = self.proxy_model.mapToSource(index)
                self.table_view.hideRow(index.row())
                record = self.table_model.record(source_index.row())
                if record.value(0) == id:
                    # Включаем редактирование для этой строки
                    self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.AllEditTriggers)
                    self.table_view.setCurrentIndex(index)
                    self.table_view.showRow(index.row())
        else:
            for row in range(self.proxy_model.rowCount()):
                self.table_view.showRow(row)
            # Если идентификатор пользователя не найден, отключаем редактирование
            self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table_model.submitAll()

    def filter_data(self):
        # Открываем диалоговое окно для выбора заголовка и текста фильтра
        dialog = FilterDialog([self.table_model.headerData(i, QtCore.Qt.Orientation.Horizontal) for i in
                               range(self.table_model.columnCount())])
        result = dialog.exec()

        if result or dialog.get_values() == 0:
            header, filter_text = dialog.get_values()

            # Ищем индекс выбранного заголовка
            column_index = [self.table_model.headerData(i, QtCore.Qt.Orientation.Horizontal) for i in
                            range(self.table_model.columnCount())].index(header)
            if column_index >= 0:
                # Применяем фильтр к прокси-модели
                self.proxy_model.setFilterKeyColumn(column_index)
                self.proxy_model.setFilterFixedString(filter_text)

    def switch_view(self):
        # Обновляем таблицу
        self.update_table()

    def update_table(self):
        # Получаем имя выбранной таблицы
        table_name = self.table_combo_box.currentText()

        self.next_index = self.tables.index(table_name)
        # Устанавливаем эту таблицу для модели
        self.table_model.setTable(table_name)
        # Выполняем выборку данных
        self.table_model.select()

    def execute_sql(self):
            # Открываем диалоговое окно для ввода SQL-запроса
            query, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Execute SQL", "Enter SQL query:")

            if ok and query:
                # Выполняем SQL-запрос и устанавливаем результат в качестве модели для представления таблицы
                self.table_model.setQuery(query)
                if self.table_model.lastError().isValid():
                    # Если возникла ошибка, выводим сообщение об ошибке
                    QtWidgets.QMessageBox.critical(self, "Execute SQL",
                                                   f"Failed to execute SQL query: {self.table_model.lastError().text()}")
                else:
                    # Если ошибки нет, устанавливаем модель для представления таблицы
                    self.table_view.setModel(self.table_model)

    def reset_table(self):
            # Сбрасываем представление таблицы до исходной модели таблицы
            self.initialize_db()

    def show_image(self, index):
        try:
            print(index.data())

            # Получите данные из выбранной ячейки
            # Если данные являются экземпляром QByteArray (что означает, что это изображение),
            # откройте диалоговое окно с изображением
            if isinstance(index.data(), QtCore.QByteArray):
                self.dialog = ImageDialog(index.data(), self)
                self.dialog.show()
            print(1)
        except Exception:
            pass


def main():
    # Создаем объект QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Создаем объект DbViewer и отображаем его
    viewer = DbViewer()
    viewer.show()

    # Запускаем основной цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    # Если скрипт запущен как основная программа, вызываем функцию main()
    main()
