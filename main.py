import flet as ft
from threading import Thread
from PIL import UnidentifiedImageError
from io import BytesIO
import os

class Rembg:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "rembg"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.theme = ft.Theme(font_family="Cantarell")

        self.page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME,
                                            label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS,
                                            label="Preferences"),
                ft.NavigationBarDestination(icon=ft.Icons.QUESTION_MARK,
                                            label="About")
            ]
        )

        # appbar (gtk headerbar)
        self.appbar = ft.AppBar(
            center_title=True,
        )
        
        # this is for loading screen
        self.loading_cons = [ft.Text('Loading rembg...', size=45, 
                                   weight=ft.FontWeight.W_900,
                                   text_align=ft.TextAlign.CENTER,
                                   width=self.page.width
                                   ),
                             ft.Text('The AI model for removing backgrounds is loading, this will take 10-20 seconds.', 
                                   text_align=ft.TextAlign.CENTER,
                                   width=self.page.width),]
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
                              ,controls=self.loading_cons,
                              )

        # main file picker for file
        self.file_picker = ft.FilePicker(on_result=self.image_file)

        # pagelet (main body)
        self.pagelet = ft.Pagelet(
            appbar=self.appbar,
            content=self.cons,
        )

        self.page.add(self.pagelet, self.file_picker)
        # this loads the rembg waiting screen
        self.required_threading()
    def required_threading(self):
        # this is for not freezing the ui on the main thread
        Thread(target=self.rembg_start, daemon=True).start()
        print("Starting rembg thread...")
    def rembg_start(self):
        # import rembg and start a new session
        import rembg
        print("imported rembg")
        self.sess = rembg.new_session()
        # this takes the rembg function-level import and puts it globally
        # not recommended, but this is the only (and easiest) way
        globals()['rembg'] = rembg
        print("rembg globalized")
        # after that, we delete the loading widgets 
        self.cons.controls.clear()
        # then add the main ones
        print("controls cleared")
        self.cons.controls.extend(self.main_cons)
        self.page.update()

    def image_file(self, e: ft.FilePickerResultEvent):
        if e.files:
           fpath = [file.path for file in e.files][0]
        print(fpath)
        with open(fpath, 'rb') as f:
            ini = f.read()
        platform = self.page.platform
        mobile = ['PagePlatform.ANDROID', 'PagePlatform.IOS']
        for lists in mobile:
            if platform == lists:
                ini = e.files[0].bytes
            else:
                with open(fpath, 'rb') as f:
                    ini = f.read()
        self.modal = None
        try:
          self.outi = rembg.remove(ini, force_return_bytes=True, session=self.sess)
        except UnidentifiedImageError:
            self.alertdialog("Failure", 
                             "Python couldn't identify this as an image.", 
                             actions=[ft.TextButton("Ok", on_click=lambda e: self.page.close(self.modal))]
                            )

        fname = os.path.basename(fpath)
        splits = os.path.splitext(fname)
        self.name = f"{splits[0]}(no-bg).png"

        self.row_cons = [ft.TextField(label="Filename", 
                                      value=self.name,
                                      width=self.page.width - 200),
                         ft.Row(controls=[ft.IconButton(icon=ft.Icons.COPY, 
                                       icon_size=20,
                                       on_click=self.copy,),
                         ft.IconButton(icon=ft.Icons.SAVE, 
                                       icon_size=20,
                                       )], alignment=ft.MainAxisAlignment.END)]
        self.img_cons = [ft.Row(controls=self.row_cons,
                                wrap=True,
                                spacing=5,)]
        self.cons.controls.clear()
        self.cons.controls.extend(self.img_cons)
        self.page.update()

    def alertdialog(self, titles, text, actions):
        # this is a wrapper function for the dialog,
        # so it doesn't have to be repeated 
        self.modal = ft.AlertDialog(
            modal=False,
            title=ft.Text(f'{titles}'),
            content=ft.Text(f'{text}'),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda e: print("Dismissed by user")
        )
        self.page.open(self.modal)
        self.page.update()

    def copy(self, data):
        self.page.set_clipboard(data)

        self.banner = ft.Banner(
            bgcolor=ft.Colors.BLUE,
            content=ft.Text(
                "Image saved to clipboard!"
            ),
            actions=[
                ft.TextButton("Ok", on_click=close)
            ]
        )

    def close(e):
        self.banner.open = False
        self.page.update()
def main(page: ft.Page):
    Rembg(page)
    page.update()

ft.app(main)
