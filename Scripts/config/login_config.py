# Configuración de login y credenciales

LOGIN_URL = "https://4am.ie/Logon.aspx?admin&ReturnUrl=%2fAdmin%2fItems.aspx"  # URL de login
ITEMS_URL = "https://4am.ie/Admin/Items.aspx"  # URL de items
USERNAME = "martinfennelly@gmail.com"
PASSWORD = "martinfennelly"  # <--- Cambia por tu contraseña real

# Selectores para los campos de login
USERNAME_FIELD = "ctl00_ContentPlaceHolderBody_username"
PASSWORD_FIELD = "ctl00_ContentPlaceHolderBody_password"
LOGIN_BUTTON = "ctl00_ContentPlaceHolderBody_Button1"
