toolbutton = """
QToolButton:pressed {
    background-color: rgb(0,107,56);
}
QToolButton:hover {
    background-color: rgb(0,178,132);
}
QToolButton:checked {
    background-color: rgb(0,178,132);
}
"""
tablewidget = """
QTableWidget::item:selected{
    background-color:transparent;
}
QTableWidget::item{
    selection-background-color:transparent;
}
"""
headerview = """
QHeaderView::section:checked{
    background-color: rgb(0,178,132); 
    color: rgb(255,255,255); 
    font-weight: bold;
}
"""