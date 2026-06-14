"""Application entry point."""

from simple_autoclicker.ui.app import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
