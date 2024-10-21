from services.session import Session  # Importa la clase Session que maneja la sesión de usuario.
from models.locations import LocationsModel  # Importa el modelo LocationsModel, que maneja las sedes.
from models.shows import ShowsModel  # Importa el modelo ShowsModel, que maneja los shows.
from models.users import UserModel  # Importa el modelo UserModel, que maneja los usuarios.
from views.admin import AdminView  # Importa la vista AdminView, que maneja las interfaces para el administrador.

class AdminController:
    def __init__(self):  # Constructor de la clase AdminController.
        # Inicializa las instancias de los modelos y la vista.
        self.session = Session()  # Instancia que maneja la sesión del usuario activo.
        self.locations_model = LocationsModel()  # Modelo que maneja las sedes.
        self.shows_model = ShowsModel()  # Modelo que maneja los shows.
        self.user_model = UserModel()  # Modelo que maneja los usuarios.
        self.admin_view = AdminView()  # Vista que muestra las interfaces del administrador.

    @property
    def locations(self):
        """Obtiene las sedes y sus IDs."""
        locations = self.locations_model.get_all()  # Obtiene todas las sedes desde el modelo.
        return locations, [loc['location_id'] for loc in locations]  # Devuelve las sedes y sus IDs.

    @property
    def shows(self):
        """Obtiene los shows y sus IDs."""
        recap = self.shows_model.get_shows_recap()  # Obtiene el resumen de los shows desde el modelo.
        return recap, [show['show_id'] for show in recap]  # Devuelve los shows y sus IDs.

    def menu(self):
        """Muestra el menú del administrador y ejecuta la opción seleccionada."""
        self.logout = False  # Estado inicial del logout.
        self.user_data = self.session.get_active_user()  # Obtiene los datos del usuario activo.
        option = self.admin_view.menu(self.user_data['name'])  # Muestra el menú de administrador.

        # Diccionario de acciones del menú.
        menu_actions = {
            1: self._handle_locations,  # Gestionar sedes.
            2: self._create_show,  # Crear un show.
            3: self._display_shows,  # Mostrar shows.
            4: self._update_show,  # Actualizar un show.
            5: self._delete_show,  # Eliminar un show.
            6: self._update_personal_info,  # Actualizar la información personal.
            7: self._log_out,  # Cerrar sesión.
            8: self._exit_system,  # Salir del sistema.
        }

        action = menu_actions.get(option)  # Obtiene la acción seleccionada.
        if action:
            action()  # Ejecuta la acción seleccionada.

        return {'log_out': self.logout}  # Devuelve el estado del logout.

    def _handle_locations(self):
        """Gestiona el submenú de sedes."""
        while True:
            locations, location_ids = self.locations  # Obtiene las sedes y sus IDs.
            option = self.admin_view.locations_menu()  # Muestra el menú de sedes.
            if option == 1:
                self.admin_view.display(locations)  # Muestra las sedes.
            elif option == 2:
                self._create_location()  # Crea una nueva sede.
            elif option == 3:
                self._update_location(location_ids)  # Actualiza una sede existente.
            elif option == 4:
                self._delete_location(location_ids)  # Elimina una sede existente.
            else:
                break  # Sale del submenú.

    def _create_location(self):
        """Crea una nueva sede."""
        data = self.admin_view.create_location()  # Solicita los datos para crear una sede.
        self.locations_model.post(data)  # Envía los datos al modelo para crear la sede.

    def _update_location(self, location_ids):
        """Actualiza una sede existente."""
        update = self.admin_view.update_location(location_ids)  # Solicita los datos para actualizar una sede.
        if update['success']:
            self.locations_model.update(update['id'], update['data'])  # Actualiza la sede en el modelo.

    def _delete_location(self, location_ids):
        """Elimina una sede existente."""
        delete = self.admin_view.delete_location(location_ids)  # Solicita la confirmación para eliminar una sede.
        if delete['success']:
            self.locations_model.delete(delete['id'])  # Elimina la sede en el modelo.
            self._delete_shows_by_location(delete['id'])  # Elimina los shows asociados a la sede eliminada.

    def _delete_shows_by_location(self, location_id):
        """Elimina los shows asociados a una sede."""
        shows = self.shows_model.get_by_location(location_id)  # Obtiene los shows asociados a la sede.
        if shows:
            for show in shows:
                self.shows_model.delete(show['show_id'])  # Elimina cada show asociado.

    def _create_show(self):
        """Crea un nuevo show."""
        locations, location_ids = self.locations  # Obtiene las sedes disponibles.
        if not location_ids:
            self.admin_view.alert('No hay sedes disponibles. Registre una primero.')  # Alerta si no hay sedes.
            return

        self.admin_view.display(locations)  # Muestra las sedes disponibles.
        location = self.admin_view.select_location(location_ids)  # Solicita la selección de una sede.
        if location['success']:
            data = self.admin_view.create_show()  # Solicita los datos del show.
            self.shows_model.create_show(data, location['id'])  # Crea el show en la sede seleccionada.

    def _display_shows(self):
        """Muestra los shows disponibles."""
        shows_recap, show_ids = self.shows  # Obtiene los shows y sus IDs.
        self.admin_view.display(shows_recap)  # Muestra el resumen de los shows.
        show = self.admin_view.select_show(show_ids)  # Solicita la selección de un show.
        if show['success']:
            details = self.shows_model.get_show_details(show['id'])  # Obtiene los detalles del show.
            self.admin_view.display(details)  # Muestra los detalles del show.

    def _update_show(self):
        """Actualiza un show existente."""
        shows_recap, show_ids = self.shows  # Obtiene los shows disponibles.
        self.admin_view.display(shows_recap)  # Muestra los shows.
        update = self.admin_view.update_show(show_ids)  # Solicita los datos para actualizar un show.
        if update['success']:
            self._apply_show_update(update)  # Aplica la actualización del show.

    def _apply_show_update(self, update):
        """Aplica la actualización a un show."""
        location_ids = self.locations[1]  # Obtiene los IDs de las sedes disponibles.
        data = update['data']  # Datos actualizados del show.
        location = self.admin_view.update_location_show(location_ids)  # Solicita la nueva sede para el show.
        if location['success']:
            data['location_id'] = location['id']  # Actualiza la sede del show.

        self.shows_model.update(update['id'], data)  # Aplica la actualización en el modelo.

    def _delete_show(self):
        """Elimina un show."""
        shows_recap, show_ids = self.shows  # Obtiene los shows disponibles.
        self.admin_view.display(shows_recap)  # Muestra los shows.
        delete = self.admin_view.delete_show(show_ids)  # Solicita la confirmación para eliminar un show.
        if delete['success']:
            self.shows_model.delete(delete['id'])  # Elimina el show.

    def _update_personal_info(self):
        """Actualiza la información personal del usuario."""
        user_data = self.user_data  # Datos actuales del usuario.
        updated_info = self.admin_view.update_user()  # Solicita los datos para actualizar.
        new_pass = self.admin_view.update_password(user_data['password'])  # Solicita la actualización de la contraseña.
        if new_pass:
            updated_info['password'] = new_pass  # Actualiza la contraseña.

        self.user_model.update(user_data['user_id'], updated_info)  # Aplica la actualización en el modelo.
        self.session.start_session(self.user_model.get_by_attribute('user_id', user_data['user_id']))  # Actualiza la sesión.

    def _log_out(self):
        """Cierra la sesión del usuario."""
        self.logout = self.admin_view.log_out()  # Cierra la sesión.

    def _exit_system(self):
        """Sale del sistema."""
        exit() if self.admin_view.exit_system() else None  # Sale del sistema si el usuario lo confirma.
