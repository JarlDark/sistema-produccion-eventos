from services.session import Session

from models.locations import LocationsModel
from models.shows import ShowsModel
from models.reservations import ReservationsModel
from models.users import UserModel

from views.attendee import AttendeeView

# Controlador para gestionar las interacciones de un asistente al sistema.
class AttendeeController:
    def __init__(self):
        # Se inicializan los modelos y la vista del asistente.
        self.session = Session()  # Maneja la sesión activa del usuario.
        self.locations_model = LocationsModel()  # Modelo de sedes.
        self.shows_model = ShowsModel()  # Modelo de shows.
        self.reservations_model = ReservationsModel()  # Modelo de reservas.
        self.user_model = UserModel()  # Modelo de usuarios.
        self.attendee_view = AttendeeView()  # Vista para mostrar la interfaz al asistente.

    @property
    def locations(self):
        """Obtiene las sedes y sus IDs."""
        # Recupera todas las sedes disponibles y sus IDs para facilitar la selección.
        locations = self.locations_model.get_all()
        return locations, [loc['location_id'] for loc in locations]

    @property
    def shows(self):
        """Obtiene los shows y sus IDs."""
        # Recupera un resumen de los shows disponibles y sus IDs.
        recap = self.shows_model.get_shows_recap()
        return recap, [show['show_id'] for show in recap]
    
    @property
    def reservations(self):
        # Obtiene el resumen de reservas del usuario actual y sus IDs.
        recap = self.reservations_model.reservations_recap(self.user_data['user_id'])
        return recap, [res['reservation_id'] for res in recap]

    def menu(self):
        # Menú principal del asistente.
        self.logout = False
        self.user_data = self.session.get_active_user()  # Obtiene los datos del usuario activo.
        option = self.attendee_view.menu(self.user_data['name'])  # Muestra el menú con el nombre del usuario.

        # Diccionario de acciones que el usuario puede ejecutar.
        menu_actions = {
            1: self._new_reservation,  # Crear nueva reserva.
            2: self._display_reservations,  # Ver reservas.
            3: self._delete_reservation,  # Eliminar una reserva.
            4: self._update_personal_info,  # Actualizar información personal.
            5: self._log_out,  # Cerrar sesión.
            6: self._exit_system,  # Salir del sistema.
        }

        # Ejecuta la acción seleccionada si es válida.
        action = menu_actions.get(option)
        if action:
            action()

        return {'log_out': self.logout}  # Retorna el estado de logout.

    def _new_reservation(self):
        # Creación de una nueva reserva.
        shows_recap, show_ids = self.shows  # Obtiene shows disponibles.
        self.attendee_view.display(shows_recap)  # Muestra la lista de shows al usuario.

        selected_show = self.attendee_view.select_show(show_ids)  # Permite seleccionar un show.
        if selected_show['success']:
            self._process_show(selected_show['id'])  # Procesa la selección.

    def _process_show(self, show_id):
        # Procesa la reserva de un show específico.
        details = self.shows_model.get_show_details(show_id)  # Obtiene los detalles del show.
        self.attendee_view.display(details)  # Muestra los detalles al usuario.
        if self.attendee_view.buy_ticket(details):  # Si el usuario decide comprar el boleto.
            self._create_reservation(details)  # Crea la reserva.

    # Este método debe ser optimizado, delegando la lógica de actualización a ReservationsModel.
    def _create_reservation(self, details):
        self.shows_model.update_reservations(1, details['show_id'])  # Actualiza el conteo de reservas.
        data = {
            'user_id': self.user_data['user_id'], 
            'show_id': details['show_id']
        }
        ticket = self.reservations_model.create_reservation(data)  # Crea la reserva.
        self.attendee_view.display_ticket(ticket)  # Muestra el boleto al usuario.

    def _display_reservations(self):
        # Muestra las reservas del usuario.
        reservations_recap, reservations_ids = self.reservations  # Obtiene el resumen de reservas.

        self.attendee_view.display(reservations_recap)  # Muestra el resumen.
        option = self.attendee_view.select_show(reservations_ids)  # Permite seleccionar una reserva.
        if option['success']:
            ticket = self.reservations_model.get_ticket_details(option['id'])  # Obtiene los detalles del boleto.
            self.attendee_view.display(ticket)  # Muestra los detalles del boleto.

    def _delete_reservation(self):
        # Elimina una reserva seleccionada por el usuario.
        reservations_recap, reservations_ids = self.reservations  # Obtiene el resumen de reservas.

        self.attendee_view.display(reservations_recap)  # Muestra el resumen.
        option = self.attendee_view.select_show(reservations_ids)  # Permite seleccionar una reserva.
        if option['success']:
            if self.attendee_view.delete_reservation():  # Si el usuario confirma la eliminación.
                res = self.reservations_model.get_by_attribute('reservation_id', option['id'])  # Obtiene la reserva.
                self.reservations_model.delete(option['id'])  # Elimina la reserva.
                self.shows_model.update_reservations(-1, res['show_id'])  # Actualiza el conteo de reservas del show.

    # Lógica duplicada con el rol de administrador, considerar centralizar esta funcionalidad.
    def _update_personal_info(self):
        # Actualización de información personal del usuario.
        user_data = self.user_data
        updated_info = self.attendee_view.update_user()  # Obtiene la nueva información.

        new_pass = self.attendee_view.update_password(user_data['password'])  # Verifica si se actualiza la contraseña.
        if new_pass:
            updated_info['password'] = new_pass

        self.user_model.update(user_data['user_id'], updated_info)  # Actualiza la información del usuario.
        self.session.start_session(self.user_model.get_by_attribute('user_id', user_data['user_id']))  # Refresca la sesión.

    def _log_out(self):
        # Cierra la sesión del usuario.
        self.logout = self.attendee_view.log_out()

    def _exit_system(self):
        # Permite salir del sistema.
        exit() if self.attendee_view.exit_system() else None
