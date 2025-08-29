import flet as ft

class Rembg:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "rembg"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.theme = ft.Theme(font_family="Cantarell")

        # appbar (gtk headerbar)
        self.appbar = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.MENU, tooltip="HWO", on_click=self.draw),
            center_title=True,
        )

        # main items for column
        self.main_cons = [ft.Text('rembg-flutter', size=45, 
                                   weight=ft.FontWeight.W_900,
                                   text_align=ft.TextAlign.CENTER,
                                   width=self.page.width
                                   ),
                          ft.Text('Remove a background, now with flutter.', 
                                   text_align=ft.TextAlign.CENTER,
                                   width=self.page.width),
                          ft.FilledButton(text='Continue w/ File', 
                                          icon=ft.Icons.START,
                                          adaptive=True,
                                          on_click= lambda _: self.file_picker.pick_files()
                                          )]

        ## main content (column)
        self.cons = ft.Column(alignment=ft.alignment.center,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER
                              ,controls=self.main_cons,
                              )

        # main file picker for file
        self.file_picker = ft.FilePicker(on_result=self.image_file)

        self.draws = ft.NavigationDrawer(
            controls=[
                ft.NavigationDrawerDestination(
                    label="Home",
                    icon=ft.Icons.HOME_FILLED
                ),
                ft.NavigationDrawerDestination(
                    label="Prefernces",
                    icon=ft.Icons.SETTINGS
                ),
                ft.NavigationDrawerDestination(
                    label="About",
                    icon=ft.Icons.QUESTION_MARK
                ),
            ]
        )
        # pagelet (main body)
        self.pagelet = ft.Pagelet(
            appbar=self.appbar,
            content=self.cons,
            drawer=self.draws
        )

        self.page.add(self.pagelet, self.draws, self.file_picker)
    def draw(self, e):
        self.page.open(self.draws) 

    def image_file(self, e: ft.FilePickerResultEvent):
        if e.files:
            for file in e.files:
                print(file.path)

def main(page: ft.Page):
    Rembg(page)
    page.update()

ft.app(main)
