import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os
import datetime
from cryptography.fernet import Fernet

class PasswordManager(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Mux Password Manager")
        self.set_border_width(10)
        self.set_default_size(1000, 600)
        self.set_icon_from_file("icon.png")
        # Load and apply CSS
        self.apply_css()

        # Initialize encryption key
        self.key = self.load_or_generate_key()
        self.fernet = Fernet(self.key)

        # App lock variables
        self.lock_timeout = 60  # seconds
        self.lock_timer = None
        self.locked = False
        self.lock_pin = None  # Variable to store the lock PIN

        # Split window with menu on the left and content on the right
        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(250)  # Set fixed width for the side menu
        self.add(self.paned)

        # Create side menu
        self.menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.menu.get_style_context().add_class("menu")

        # Center align menu within the window
        alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        alignment.add(self.menu)
        self.paned.pack1(alignment, False, True)

        # Logo and application name
        logo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        logo_label = Gtk.Label(label="\n<span font='large' weight='bold'>Mux</span>\n"
                                      "<span font='large' weight='bold'>Password Manager</span>\n"
                                      "<span font='large'>Version: 1.0</span>\n")
        logo_label.set_use_markup(True)
        logo_label.set_justify(Gtk.Justification.CENTER)
        logo_box.pack_start(logo_label, False, False, 0)
        self.menu.pack_start(logo_box, False, False, 0)

        # Add menu items
        self.create_menu_item("Home", self.show_home_page)
        self.create_menu_item("Passwords", self.show_passwords_page)
        self.create_menu_item("Add a Password", self.show_add_a_password_page)
        self.create_menu_item("Settings", self.show_settings_page)
        self.create_menu_item("About", self.show_about_page)
        self.create_menu_item("Help", self.show_help_page)

        # Create content area
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.content.get_style_context().add_class("content")
        self.paned.pack2(self.content, True, True)

        # Show home page initially
        self.show_home_page()

        # Start the lock timer
        self.start_lock_timer()

        # Connect destroy event
        self.connect("destroy", self.on_destroy)

    def apply_css(self):
        style_provider = Gtk.CssProvider()
        style_provider.load_from_path("style.css")

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Style for the main window
        self.get_style_context().add_class("main-window")

    def load_or_generate_key(self):
        key_file = "secret.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        return key

    def create_menu_item(self, label, callback):
        button = Gtk.Button(label=label)
        button.set_size_request(200, 50)
        button.connect("clicked", self.check_pin_required(callback))
        button.get_style_context().add_class("menu-item")
        self.menu.pack_start(button, False, False, 0)

    def check_pin_required(self, callback):
        def wrapper(widget):
            if self.locked and self.lock_pin:
                self.lock_app()
            else:
                callback(widget)
        return wrapper

    def show_home_page(self, widget=None):
        self.set_content("")

        # Welcome message
        welcome_label = Gtk.Label(label="<span font='x-large' weight='bold'>Welcome to Mux Password Manager</span>\n\n\n")
        welcome_label.set_use_markup(True)
        welcome_label.set_justify(Gtk.Justification.CENTER)

        # Clock display
        self.clock_label = Gtk.Label(label="")
        self.clock_label.set_use_markup(True)
        self.update_clock()  # Initial update

        GLib.timeout_add_seconds(1, self.update_clock)  # Update every second

        # Buttons
        see_passwords_button = Gtk.Button(label="See Passwords")
        add_password_button = Gtk.Button(label="Add a New Password")

        see_passwords_button.connect("clicked", self.check_pin_required(self.show_passwords_page))
        add_password_button.connect("clicked", self.check_pin_required(self.show_add_a_password_page))

        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.pack_start(see_passwords_button, True, True, 0)
        buttons_box.pack_start(add_password_button, True, True, 0)

        # Vertical box for alignment
        vertical_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vertical_box.pack_start(welcome_label, False, False, 0)
        vertical_box.pack_start(self.clock_label, False, False, 0)
        vertical_box.pack_start(buttons_box, False, False, 0)

        # Horizontal alignment for centering
        horizontal_alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        horizontal_alignment.add(vertical_box)

        self.content.pack_start(horizontal_alignment, True, True, 0)
        self.content.show_all()

    def update_clock(self):
        now = datetime.datetime.now()
        formatted_time = now.strftime("%H:%M")
        self.clock_label.set_label(formatted_time)
        return True  # Returning True ensures the function is called again

    def show_passwords_page(self, widget=None):
        if self.locked and self.lock_pin:
            self.lock_app()
            return

        self.set_content("")

    # Load passwords
        passwords = self.load_passwords()

    # Scrolled window to contain passwords
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.content.pack_start(scrolled_window, True, True, 0)

    # Box for organizing passwords
        passwords_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_window.add(passwords_box)

        for password in passwords:
            name = password['name']
            link = password['link']
            encrypted_password = password['password']
            decrypted_password = self.decrypt_password(encrypted_password)

            # Password name
            name_label = Gtk.Label(label=f"<span font='x-large' weight='bold'>Name:</span> {name}")
            name_label.set_use_markup(True)
            passwords_box.pack_start(name_label, False, False, 0)

        # Link (if available)
            if link:
                link_label = Gtk.Label(label=f"<span font='x-large' weight='bold'>Link:</span> {link}")
                link_label.set_use_markup(True)
                passwords_box.pack_start(link_label, False, False, 0)

        # Display password as asterisks by default
            password_label = Gtk.Label(label=f"<span font='x-large' weight='bold'>Password:</span> {'*' * len(decrypted_password)}")
            password_label.set_use_markup(True)

        # Align password label to center
            password_alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
            password_alignment.add(password_label)

            passwords_box.pack_start(password_alignment, False, False, 0)

        # Buttons for operations
            buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
            show_button = Gtk.Button(label="Show")
            edit_button = Gtk.Button(label="Edit")
            delete_button = Gtk.Button(label="Delete")

            show_button.connect("clicked", self.show_password_handler, decrypted_password)
            edit_button.connect("clicked", self.edit_password, password)
            delete_button.connect("clicked", self.delete_password, password)

            buttons_box.pack_end(show_button, False, False, 0)
            buttons_box.pack_end(edit_button, False, False, 0)
            buttons_box.pack_end(delete_button, False, False, 0)

            passwords_box.pack_start(buttons_box, False, False, 0)

            # Horizontal separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            passwords_box.pack_start(separator, False, False, 5)

        self.content.show_all()


    def show_password_handler(self, widget, decrypted_password):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"Password: {decrypted_password}"
        )
        dialog.set_title("Decrypted Password")
        dialog.run()
        dialog.destroy()

    def show_add_a_password_page(self, widget=None):
        if self.locked and self.lock_pin:
            self.lock_app()
            return

        self.set_content("")

        # Labels and entry fields
        name_label = Gtk.Label(label="Name:")
        self.name_entry = Gtk.Entry()

        link_label = Gtk.Label(label="Link (optional):")
        self.link_entry = Gtk.Entry()

        password_label = Gtk.Label(label="Password:")
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)  # Hide password input

        add_button = Gtk.Button(label="Add Password")
        add_button.connect("clicked", self.add_password)

        # Box for organizing widgets
        add_password_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        add_password_box.pack_start(name_label, False, False, 0)
        add_password_box.pack_start(self.name_entry, False, False, 0)
        add_password_box.pack_start(link_label, False, False, 0)
        add_password_box.pack_start(self.link_entry, False, False, 0)
        add_password_box.pack_start(password_label, False, False, 0)
        add_password_box.pack_start(self.password_entry, False, False, 0)
        add_password_box.pack_start(add_button, False, False, 0)

        # Center align add password box
        add_password_alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        add_password_alignment.add(add_password_box)

        self.content.pack_start(add_password_alignment, True, True, 0)
        self.content.show_all()

    def add_password(self, widget):
        name = self.name_entry.get_text()
        link = self.link_entry.get_text()
        password = self.password_entry.get_text()

        if not name or not password:
            self.show_message_dialog("Error", "Please enter name and password.")
            return

        encrypted_password = self.encrypt_password(password)
        new_password = {'name': name, 'link': link, 'password': encrypted_password}

        passwords = self.load_passwords()
        passwords.append(new_password)
        self.save_passwords(passwords)

        self.show_message_dialog("Success", "Password added successfully.")

        # Clear entries
        self.name_entry.set_text("")
        self.link_entry.set_text("")
        self.password_entry.set_text("")

    def show_settings_page(self, widget=None):
        self.set_content("")

        # Page title
        title_label = Gtk.Label(label="<span font='x-large' weight='bold'>Settings</span>")
        title_label.set_use_markup(True)

        # Form elements for PIN
        pin_label = Gtk.Label(label="Enter 4-digit PIN:")
        pin_entry = Gtk.Entry()
        pin_entry.set_visibility(False)
        pin_entry.set_max_length(4)

        save_button = Gtk.Button(label="Save PIN")
        save_button.connect("clicked", self.save_pin, pin_entry)

        # Vertical box for form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form_box.pack_start(title_label, False, False, 0)
        form_box.pack_start(pin_label, False, False, 0)
        form_box.pack_start(pin_entry, False, False, 0)
        form_box.pack_start(save_button, False, False, 0)

        # Center align form box
        form_alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        form_alignment.add(form_box)

        self.content.pack_start(form_alignment, True, True, 0)
        self.content.show_all()

    def toggle_pin_enabled(self, checkbox):
        if checkbox.get_active():
            # Enable PIN entry
            self.show_settings_page()
        else:
            # Disable PIN entry
            self.lock_pin = None  # Clear stored PIN
            self.show_settings_page()

    def save_pin(self, widget, pin_entry):
        pin = pin_entry.get_text()
        if len(pin) == 4 and pin.isdigit():
            self.lock_pin = pin
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="PIN saved successfully."
            )
            dialog.set_title("Success")
            dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Invalid PIN. Please enter a 4-digit numeric PIN."
            )
            dialog.set_title("Error")
            dialog.run()
            dialog.destroy()

    def reset_settings(self, widget):
        self.lock_pin = None
        self.show_message_dialog("Success", "Settings reset successfully.")

    def show_about_page(self, widget=None):
        self.set_content("")

        about_label = Gtk.Label(label="""
        <span font='x-large' weight='bold' foreground='#00afef'>Mux Password Manager</span>\n
        <span font='large'>Version: 1.0</span>\n
        <span>This is the Mux Password Manager application created by Muhammed Šehić.</span>\n\n
        <span><a href='https://github.com/MuxBH28'>GitHub</a></span>\n
        <span><a href='https://sehic.rf.gd/'>Website</a></span>\n\n
        <span>Copyright © 2024 Muhammed Šehić</span>\n
        """)
        about_label.set_use_markup(True)
        about_label.set_justify(Gtk.Justification.CENTER)

        self.content.pack_start(about_label, True, True, 0)
        self.content.show_all()

    def show_help_page(self, widget=None):
        self.set_content("")

        help_label = Gtk.Label(label="<span font='x-large' weight='bold'>Help - Mux Password Manager</span>\n\n"
                                      "<b>Home:</b>\n"
                                      "Displays a welcome message and the current time. You can navigate to the passwords page or add a new password from here.\n\n"
                                      "<b>Passwords:</b>\n"
                                      "Displays a list of saved passwords. You can view, edit, or delete passwords.\n\n"
                                      "<b>Add a Password:</b>\n"
                                      "Allows you to add a new password with optional link.\n\n"
                                      "<b>Settings:</b>\n"
                                      "Allows you to set a 4-digit PIN to lock the application.\n\n"
                                      "<b>About:</b>\n"
                                      "Displays information about the application and developer.\n\n"
                                      "<b>Lock App:</b>\n"
                                      "Locks the application and requires the PIN to unlock.\n"
                                      "For any issues or queries, contact support at support@muxpasswordmanager.com.\n")
        help_label.set_use_markup(True)
        help_label.set_justify(Gtk.Justification.CENTER)

        self.content.pack_start(help_label, True, True, 0)
        self.content.show_all()

    def set_content(self, content):
        self.content.foreach(lambda widget: self.content.remove(widget))
        if content:
            self.content.add(Gtk.Label(label=content))
        self.content.show_all()

    def lock_app(self):
        self.set_content("")
        self.show_message_dialog("Locked", "Application locked. Enter PIN to unlock.")
        self.unlock_timer = None
        self.locked = True

    def start_lock_timer(self):
        if self.lock_timeout > 0:
            self.lock_timer = GLib.timeout_add_seconds(self.lock_timeout, self.lock_app)

    def unlock_app(self, pin):
        if pin == self.lock_pin:
            self.locked = False
            self.start_lock_timer()
            self.show_message_dialog("App Unlocked", "The application is unlocked.")
        else:
            self.show_message_dialog("Invalid PIN", "Invalid PIN. Please try again.")

    def on_destroy(self, *args):
        Gtk.main_quit()

    def encrypt_password(self, password):
        return self.fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password):
        return self.fernet.decrypt(encrypted_password).decode()

    def load_passwords(self):
        passwords_file = "passwords.csv"
        passwords = []
        if os.path.exists(passwords_file):
            with open(passwords_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    name, link, encrypted_password = line.strip().split(",")
                    passwords.append({
                        'name': name,
                        'link': link,
                        'password': encrypted_password.encode()
                    })
        return passwords

    def save_passwords(self, passwords):
        passwords_file = "passwords.csv"
        with open(passwords_file, "w") as f:
            for password in passwords:
                name = password['name']
                link = password['link']
                encrypted_password = password['password'].decode()
                f.write(f"{name},{link},{encrypted_password}\n")

    def edit_password(self, widget, password_info):
        dialog = Gtk.Dialog(title="Edit Password", transient_for=self, flags=0, buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        name_label = Gtk.Label(label="Name:")
        name_entry = Gtk.Entry()
        name_entry.set_text(password_info["name"])
        dialog.vbox.pack_start(name_label, True, True, 0)
        dialog.vbox.pack_start(name_entry, True, True, 0)

        link_label = Gtk.Label(label="Link (optional):")
        link_entry = Gtk.Entry()
        link_entry.set_text(password_info["link"])
        dialog.vbox.pack_start(link_label, True, True, 0)
        dialog.vbox.pack_start(link_entry, True, True, 0)

        password_label = Gtk.Label(label="Password:")
        password_entry = Gtk.Entry()
        password_entry.set_text(self.decrypt_password(password_info["password"]))
        password_entry.set_visibility(False)  # Hide password input
        dialog.vbox.pack_start(password_label, True, True, 0)
        dialog.vbox.pack_start(password_entry, True, True, 0)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            new_name = name_entry.get_text()
            new_link = link_entry.get_text()
            new_password = password_entry.get_text()

            if new_name != password_info["name"] or new_link != password_info["link"] or new_password:
                encrypted_password = self.encrypt_password(new_password)
                updated_password = {
                    "name": new_name,
                    "link": new_link,
                    "password": encrypted_password
                }

                passwords = self.load_passwords()
                index = passwords.index(password_info)
                passwords[index] = updated_password
                self.save_passwords(passwords)

                self.show_message_dialog("Success", "Password updated successfully.")
                self.show_passwords_page()
            else:
                self.show_message_dialog("Information", "No changes made.")
        dialog.destroy()

    def delete_password(self, widget, password_info):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format=f"Do you want to delete the password for '{password_info['name']}'?"
        )
        dialog.set_title("Confirm Deletion")

        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            passwords = self.load_passwords()
            passwords.remove(password_info)
            self.save_passwords(passwords)
            self.show_message_dialog("Success", "Password deleted successfully.")
            self.show_passwords_page()
        dialog.destroy()

    def show_message_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.set_title(title)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    win = PasswordManager()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
