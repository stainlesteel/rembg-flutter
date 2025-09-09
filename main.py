import flet as ft
from threading import Thread
from PIL import UnidentifiedImageError
from io import BytesIO
import os
import base64
from functools import partial

os.environ['REMBG_HOME'] = ft.app_dir + "/assets/u2net.onnx"

class Rembg:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "rembg"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.theme = ft.Theme(font_family="Cantarell")
        self.page.expand = True

        self.page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME,
                                            label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS,
                                            label="Preferences"),
                ft.NavigationBarDestination(icon=ft.Icons.QUESTION_MARK,
                                            label="About")
            ],
            on_change=self.on_nav_change,
            selected_index=0
        )
        # this is for about page
        self.version = '1.0.0'

        if self.page.client_storage.contains_key('theme'):
            theme = self.page.client_storage.get('theme')
            self.theme_val = theme
            if theme.upper() == 'DARK':
                self.page.theme_mode = ft.ThemeMode.DARK
            if theme.upper() == 'LIGHT':
                self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.update()
        else:
            self.theme_val = 'System'
        # appbar (gtk headerbar)
        self.appbar = ft.AppBar(
            center_title=True,
        )
        # this is for loading screen
        self.loading_cons = [ft.Text('Loading rembg...', size=45, 
                                   weight=ft.FontWeight.W_900,
                                   text_align=ft.TextAlign.CENTER
                                   ),
                             ft.Text('The AI model for removing backgrounds is loading, this will take 10-20 seconds.', 
                                   text_align=ft.TextAlign.CENTER,)]
        # main items for column
        self.main_cons = [ft.Text('rembg-flutter', size=45, 
                                   weight=ft.FontWeight.W_900,
                                   text_align=ft.TextAlign.CENTER
                                   ),
                          ft.Text('Remove a background, now with flutter.', 
                                   text_align=ft.TextAlign.CENTER,),
                          ft.FilledButton(text='Continue w/ File', 
                                          icon=ft.Icons.START,
                                          adaptive=True,
                                          on_click= lambda _: self.file_picker.pick_files()
                                          )]
        self.credits_cons = "Created by stainlesteel.\n Licensed under the GNU General Public License v3, \nrefer to it for details on usage, distribution, and copying."
        
        self.about_cons = [
                             ft.Text(
                                 'rembg-flutter',
                                 size=45,
                                 weight=ft.FontWeight.W_900,
                                 text_align=ft.TextAlign.CENTER
                             ),
                             ft.Text(
                                 'a simple project to use the rembg library,\nby stainlesteel',
                                 text_align=ft.TextAlign.CENTER,
                                 size=25
                             ),
                             ft.FilledTonalButton(content=ft.Text(f'{self.version}')),
                             ft.Card(
                                 ft.Container(
                                     content=ft.ListTile(
                                         leading=ft.Icon(ft.Icons.WARNING),
                                         title=ft.Text("Report an issue", size=20, weight=ft.FontWeight.W_500),
                                         trailing=ft.Icon(ft.Icons.LINK),
                                         url="https://example.com"
                                     ),
                                     margin=ft.margin.all(5)
                                 )
                             ),
                             ft.Card(
                                 ft.Container(
                                     content=ft.Column([ft.ListTile(
                                         leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE),
                                         title=ft.Text("Credits", size=20, weight=ft.FontWeight.W_500),
                                         trailing=ft.IconButton(
                                             icon=ft.Icons.ARROW_RIGHT,
                                             on_click=self.credits
                                         )
                                        ),
                                        ft.ListTile(
                                              leading=ft.Icon(ft.Icons.PAGEVIEW),
                                              title=ft.Text("Website", size=20, weight=ft.FontWeight.W_500),
                                              trailing=ft.IconButton(icon=ft.Icons.LINK),
                                              url="https://example.com"
                                             )
                                                        ]),
                                     margin=ft.margin.all(5)
                                    )
                                 )
        ]
       #for the about page

        # for dropdown theme list
        self.themes = ['System', 'Light', 'Dark']
        self.ops = []
        for theme in self.themes:
            self.ops.append(
                ft.DropdownOption(
                    key=theme,
                    content=ft.Text(value=theme)
                )
            )
        # for the settings page
        self.settings_cons = [
             ft.Text(
                 'Preferences',
                 size=45,
                 weight=ft.FontWeight.W_900,
                 text_align=ft.TextAlign.CENTER
             ),
             ft.Card(
                 ft.Container(
                     content=ft.Column([ft.ListTile(
                         leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE),
                         title=ft.Text("Colour Scheme", size=20, weight=ft.FontWeight.W_500),
                         trailing=ft.Dropdown(
                            label=self.theme_val,
                            options=self.ops,
                            on_change=self.set_theme
                        )
                        ),
                                        ]),
                     margin=ft.margin.all(5)
                    )
                 )
        ]

        self.modal = None
        ## main content (column)
        self.cons = ft.Column(alignment=ft.alignment.center,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                              controls=self.loading_cons,
                              expand=True,
                              scroll='always'
                              )
        # this is a container, to properely resize contents
        self.coan = ft.Container(expand=True,
                                 content=self.cons,
                                 alignment=ft.alignment.center,
                                 )

        # main file picker for file
        self.file_picker = ft.FilePicker(on_result=self.image_file)

        # pagelet (main body)
        self.pagelet = ft.Pagelet(
            appbar=self.appbar,
            content=self.coan,
        )
        self.index = None
        self.page.add(self.pagelet, self.file_picker)
        # this loads the rembg waiting screen
        self.required_threading()
    def required_threading(self):
        # this is for not freezing the ui on the main thread
        Thread(target=self.rembg_start, daemon=True).start()
        print("Starting rembg thread...")
    def on_page_resize(self, e):
        # this is for the container
        self.page.update()
    def set_theme(self, e):
        theme = e.control.value
        self.page.client_storage.set('theme', theme)

        if theme.upper() == 'DARK':
            self.page.theme_mode = ft.ThemeMode.DARK
        if theme.upper() == 'LIGHT':
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
    def on_nav_change(self, e):
        self.cons.controls.clear()
        self.index = e.control.selected_index
        print(f'index: {self.index}')
        if self.index == 0:
            if not self.sess:
                self.cons.controls.extend(self.loading_cons)
            if hasattr(self, 'img_cons'):
                self.appbar.leading = ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Go Back to Menu",
                        on_click=partial(self.back)
                    )
                self.cons.controls.extend(self.img_cons)
            else:
                self.appbar.leading = None
                self.cons.controls.extend(self.main_cons)
        elif self.index == 1:
            self.appbar.leading = None
            self.cons.controls.extend(self.settings_cons)
        elif self.index == 2:
            self.appbar.leading = None
            self.cons.controls.extend(self.about_cons)
        self.page.update()
    def credits(self, e):
        self.alertdialog('Credits',
                         f'{self.credits_cons}',
                         actions=[ft.TextButton("Ok", on_click=lambda e: self.page.close(self.modal))])
    def rembg_start(self):
        # import rembg and start a new session
        import rembg
        print("imported rembg")
        u2_path = os.path.join(os.path.dirname(__file__), "assets", "u2net.onnx")
        self.sess = rembg.new_session("u2net_custom", model_path=u2_path)
        # this takes the rembg function-level import and puts it globally
        # not recommended, but this is the only (and easiest) way
        globals()['rembg'] = rembg
        print("rembg globalized")
        # after that, we delete the loading widgets 
        # then add the main ones

        # this is for not switching userview if they aren't in the main page
        if self.index == None:
            self.cons.controls.clear()
            print("controls cleared")
            self.cons.controls.extend(self.main_cons)
        self.page.update()

    def image_file(self, e: ft.FilePickerResultEvent):
        if e.files:
           fpath = [file.path for file in e.files][0]
        print(fpath)
        platform = self.page.platform
        mobile = ['PagePlatform.ANDROID', 'PagePlatform.IOS']
        for lists in mobile:
            if platform == lists:
                self.ini = e.files[0].bytes
            else:
                with open(fpath, 'rb') as f:
                    self.ini = f.read()
        self.modal = None
        try:
            self.outi = rembg.remove(self.ini, force_return_bytes=True, session=self.sess)
        except UnidentifiedImageError:
            self.alertdialog("Failure", 
                             "Python couldn't identify this as an image.", 
                             actions=[ft.TextButton("Ok", on_click=lambda e: self.page.close(self.modal))]
                            )

        fname = os.path.basename(fpath)
        splits = os.path.splitext(fname)
        self.name = f"{splits[0]}(no-bg).png"

        buffer = BytesIO(self.outi)
        self.b64_outi = base64.b64encode(buffer.getvalue()).decode()
        self.extra()

    def on_textbox_change(self, e):
        mango = e.control.value
        self.name = mango
    def extra(self):
        # look at that indentation!
        self.img_cons = [ft.ListTile(title=ft.TextField(label="Filename", 
                                     value=self.name,
                                     on_change=self.on_textbox_change
                                     ),
                                     trailing=ft.PopupMenuButton(
                                        icon=ft.Icons.MORE_VERT,
                                        items=[
                                            ft.PopupMenuItem(icon=ft.Icons.COPY,
                                                             text="Copy",
                                                             on_click=partial(self.copy)),
                                            ft.PopupMenuItem(icon=ft.Icons.SAVE,
                                                             text="Save",
                                                             on_click=partial(self.save))
                                        ]
                                     )),
                         ft.Image(
                            src_base64=self.b64_outi,
                            fit=ft.ImageFit.CONTAIN,
                         )]
        self.cons.controls.clear()
        self.cons.controls.extend(self.img_cons)

        self.appbar.leading = ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Go Back to Menu",
                on_click=partial(self.back)
            )
        self.page.update()
    def back(self, e):
        self.cons.controls.clear()
        self.cons.controls.extend(self.main_cons)
        self.appbar.leading = None
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

    def copy(self, e):
        self.modal = None
        self.alertdialog(
            titles="Copied!",
            text="Copied to clipboard as a base64 hash.",
            actions=[ft.TextButton("Ok", on_click=lambda e: self.page.close(self.modal))]
        )
        self.page.set_clipboard(self.b64_outi)

    def save(self, e):

        def save_file(e: ft.FilePickerResultEvent):
            if e.path:
                with open(e.path, "wb") as f:
                    f.write(self.outi)
                print('file written')
                diag()

        def diag():
            self.modal = None
            self.alertdialog(
                titles="Saved!",
                text="Saved to your device as a PNG file.",
                actions=[ft.TextButton("Ok", on_click=lambda e: self.page.close(self.modal))]
            )

        self.fpicker = ft.FilePicker(on_result=save_file)

        self.page.add(self.fpicker)
        self.fpicker.save_file(
                dialog_title="Save as...",
                file_name=self.name,
        )

def main(page: ft.Page):
    Rembg(page)
    page.update()

ft.app(target=main, assets_dir="assets")
