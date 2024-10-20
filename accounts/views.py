from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import TemplateView
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from bson import ObjectId
import firebase_admin
from firebase_admin import auth, credentials, delete_app, exceptions
from firebase_admin.exceptions import NotFoundError, FirebaseError
from pymongo import MongoClient
from .firebase_config import auth, database, firebase
from .models import Usuario
import base64
from django.shortcuts import redirect

from django.http import HttpResponse
from pymongo import MongoClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
from collections import Counter
from django.shortcuts import render
from reportlab.lib import colors
from datetime import datetime



from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Line
from reportlab.graphics import renderPDF
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.shapes import Drawing
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from reportlab.lib.enums import TA_LEFT

# Inicializar la conexión de MongoDB

client = MongoClient('mongodb+srv://gouudec2024:gou22024@gouv2.fbdwx.mongodb.net/?retryWrites=true&w=majority&appName=GoUv2')
db = client['GoUV2']


'''.........................................................vistas generales...........................................................'''

class HomePageView(TemplateView):
    template_name = 'accounts/index.html'

def calculadora(request):
    collection_viajes = db['HistorialDeRutas']
    collection_historico = db['HistoricoDeRutas']
   
    total_viajes = collection_viajes.count_documents({})
 
    emisiones_por_km = 0.143
 
    total_distancias = collection_historico.aggregate([
        {"$group": {"_id": None, "total_km": {"$sum": "$kilometraje"}, "total_viajes": {"$sum": 1}}}
    ])
   
    total_km = 0
    total_rutas = 0
    for result in total_distancias:
        total_km = result['total_km']
        total_rutas = result['total_viajes']
   
    if total_rutas > 0:
        promedio_distancia_km = total_km / total_rutas
    else:
        promedio_distancia_km = 10
   
    emisiones_evitadas = total_viajes * promedio_distancia_km * emisiones_por_km
 
    context = {
        'total_viajes': total_viajes,
        'emisiones_evitadas': emisiones_evitadas,
        'promedio_distancia_km': promedio_distancia_km
    }
 
    return render(request, 'accounts/about.html', context)

class descargaPageView(TemplateView):
    template_name = 'accounts/descarga.html'

class ContactPageView(TemplateView):
    template_name = 'accounts/contact.html'

class LoginPageView(TemplateView):
    template_name = 'accounts/login.html'


def principal(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})

    if usuario:
        rol = usuario['rol']
        image_data = usuario['foto']
        return render(request, 'accounts/principal.html', {'rol': rol, 'image_data': image_data, 'usuario': usuario})
    return render(request, 'accounts/principal.html')
    

class recu_contraPageView(TemplateView):
    template_name = 'accounts/recu_contra.html'


@csrf_protect
def send_email(request):
    if request.method == 'POST':
        print("Método POST recibido.")

        # Obtener los valores del formulario
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_content = request.POST.get('message', '').strip()

        # Imprimir los valores obtenidos del formulario
        print(f"Nombre: {name}")
        print(f"Email: {email}")
        print(f"Asunto: {subject}")
        print(f"Contenido del mensaje: {message_content}")

        # Verificar si algún campo está vacío
        if not name or not email or not subject or not message_content:
            print("Faltan campos requeridos. Redireccionando...")
            messages.error(request, 'Por favor, completa todos los campos requeridos.')
            return redirect('contact')  

        # Crear el contenido del mensaje a enviar
        message = f"De: {name}\nEmail: {email}\nMensaje:\n\n{message_content}"
        print(f"Mensaje a enviar: {message}")

        try:
            # Intentar enviar el correo
            send_mail(
                subject,                    
                message,                    
                'gou2udec@gmail.com',       
                ['gou2udec@gmail.com'],     
                fail_silently=False,        
            )
            
            print("Correo enviado correctamente.")
            messages.success(request, 'Correo enviado correctamente.')
            return redirect('contact') 
        except Exception as e:
            # Si ocurre un error, imprimir el error
            print(f"Error al enviar el correo: {e}")
            messages.error(request, 'Error al enviar el correo. Intenta nuevamente más tarde.')
            return redirect('contact') 
    else:
        print("Método no es POST, redireccionando...")
        return redirect('contact')





'''...............................................vistas específicas........................................................................'''

# Muestra la lista de administradores (Bloqueados y sin bloquear).
def cuentas(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})
    if usuario:
        rol = usuario['rol']
        image_data = usuario['foto']
        if rol != 'Súper Administrador':
            messages.error(request, 'Acceso denegado: No cuenta con los permisos necesarios para visualizar esta sección.')
            return redirect('principal')

    

    collection = db['GoUadmin']

    try:
        all_users = collection.find()
        users_blocked = [
            {
                'id': str(user.get('_id')),  
                'nombre': user.get('nombre'),
                'apellido': user.get('apellido'),
                'rol': user.get('rol'),
                'email': user.get('correo')
            }
            for user in all_users if user.get('bloqueado') == True
        ]

        users = collection.find({'bloqueado': {'$ne': True}})
        user_list = [
            {
                'id': str(user.get('_id')),  
                'nombre': user.get('nombre'),
                'apellido': user.get('apellido'),
                'rol': user.get('rol'),
                'email': user.get('correo')
            }
            for user in users
        ]

        return render(request, 'accounts/cuentas.html', {'users_blocked': users_blocked, 'user_list': user_list, 'rol': rol, 'image_data': image_data, 'usuario': usuario})
    


    except Exception as e:
        messages.error(request, f'Ocurrió un error al obtener la lista de usuarios: {e}')
        return render(request, 'accounts/cuentas.html', {'users_blocked': [], 'user_list': []})



# Maneja el inicio de sesión usando Firebase Authentication y verifica el usuario en MongoDB. 
def login_view(request):
    if request.method == 'POST':
        auth = firebase.auth()
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session_id = user['idToken']
            request.session['uid'] = str(session_id)

            request.session['email'] = email

            collection = db['GoUadmin']

            usuario = collection.find_one({'correo': email})

            if usuario:
                rol = usuario['rol']
                image_data = usuario['foto']
                return render(request, 'accounts/principal.html', {'rol': rol, 'image_data': image_data, 'usuario': usuario})
            else:
                message = "Usuario no encontrado en la base de datos"
                return render(request, 'accounts/login.html', {"message": message})

        except Exception as e:
            message = "Credenciales inválidas o error en la autenticación"
            return render(request, 'accounts/login.html', {"message": message})

    return render(request, 'accounts/login.html')


# Visualizar el apartado de configuración
def config(request):
    email = request.session.get('email')

    if not email:
        messages.error(request, 'Debe iniciar sesión primero.')
        return redirect('login')

    if request.method == 'POST':
        nombre = request.POST.get('name')
        apellido = request.POST.get('surname')
        password = request.POST.get('password')
        foto = request.FILES.get('photo')

        collection = db['GoUadmin']

        if not firebase_admin._apps:
            cred = credentials.Certificate('gou-adm-firebase-adminsdk-3hxpk-c216f44ec9.json')
            firebase_admin.initialize_app(cred)

        try:
            update_data = {}
            if nombre:
                update_data["nombre"] = nombre
            if apellido:
                update_data["apellido"] = apellido
            if foto:
                foto_base64 = base64.b64encode(foto.read()).decode('utf-8')
                update_data["foto"] = foto_base64

            if update_data:
                collection.update_one({"correo": email}, {"$set": update_data})

            if password:
                user = auth.get_user_by_email(email)
                auth.update_user(user.uid, password=password)

            messages.success(request, 'Datos actualizados exitosamente.')

        except Exception as e:
            messages.error(request, f'Error al actualizar los datos: {str(e)}')

        return redirect('login')
    
    return render(request, 'accounts/config.html')


# Visualizar los usuarios.
def usuario(request):
    usuarios_collection = db['Usuarios']
    invitados_collection = db['UsuarioInvitado']
    
    try:
        usuarios = list(usuarios_collection.find({}, {'_idusuario': 1, 'nombre': 1, 'apellidos': 1, 'telefono': 1, 'email': 1, 'bloqueado': 1}))
        invitados = list(invitados_collection.find({}, {'_idusuario': 1, 'nombre': 1, 'apellidos': 1, 'telefono': 1, 'email': 1, 'bloqueado': 1}))

        for usuario in usuarios:
            usuario['idusuario'] = usuario.pop('_idusuario')
        for invitado in invitados:
            invitado['idusuario'] = invitado.pop('_idusuario')

        usuarios_blocked = [
            {
                'idusuario': user.get('idusuario'),
                'nombre': user.get('nombre'),
                'apellidos': user.get('apellidos'),
                'telefono': user.get('telefono'),
                'email': user.get('email')
            }
            for user in usuarios if user.get('bloqueado') == True
        ]

        usuarios_not_blocked = [
            {
                'idusuario': user.get('idusuario'),
                'nombre': user.get('nombre'),
                'apellidos': user.get('apellidos'),
                'telefono': user.get('telefono'),
                'email': user.get('email')
            }
            for user in usuarios if user.get('bloqueado') != True
        ]

        invitados_blocked = [
            {
                'idusuario': guest.get('idusuario'),
                'nombre': guest.get('nombre'),
                'apellidos': guest.get('apellidos'),
                'telefono': guest.get('telefono'),
                'email': guest.get('email')
            }
            for guest in invitados if guest.get('bloqueado') == True
        ]

        invitados_not_blocked = [
            {
                'idusuario': guest.get('idusuario'),
                'nombre': guest.get('nombre'),
                'apellidos': guest.get('apellidos'),
                'telefono': guest.get('telefono'),
                'email': guest.get('email')
            }
            for guest in invitados if guest.get('bloqueado') != True
        ]
        combined_blocked = usuarios_blocked + invitados_blocked

        email = request.session.get('email')
        usuario = db['GoUadmin'].find_one({'correo': email})
        if usuario:
            rol = usuario['rol']
            image_data = usuario['foto']
            return render(request, 'accounts/usuario.html', {
                'combined_blocked': combined_blocked,
                'usuarios_not_blocked': usuarios_not_blocked,
                'invitados_not_blocked': invitados_not_blocked, 
                'rol': rol, 
                'image_data': image_data, 
                'usuario': usuario
        })

    except Exception as e:
        return render(request, 'accounts/usuario.html', {'error': str(e)})



# Visualizar los documentos
def documento(request):
    collection_registros = db['RegistrosAutos']
    collection_admin = db['GoUadmin']
    collection_politicas = db['Politi_Acuer_otros']
  
    email = request.session.get('email')
    usuario = collection_admin.find_one({'correo': email})

    registros = list(collection_registros.find({'RespuestaAprobacion': False, 'Rechazado': False}))

    for registro in registros:
        registro['idusuario'] = registro.pop('_idusuario', None)
        registro['id'] = str(registro['_id']) 

    politicas = collection_politicas.find_one({}, {'Costo_Km': 1})  
    costo_km_actual = politicas.get('Costo_Km', 0) 
    contexto = {'registros': registros, 'costo_km_actual': costo_km_actual}  

    if usuario:
        contexto.update({'rol': usuario['rol'], 'image_data': usuario['foto'], 'usuario': usuario})

    return render(request, 'accounts/documento.html', contexto)



# Visualizar las reseñas
def resena(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})

    collection = db['HistorialDeRutas']
    
    pipeline = [
        {
            '$match': {
                '$or': [
                    {'reservasInfo.revisada': {'$ne': True}},
                    {'cumplioRutaInfoPasajeros.revisada': {'$ne': True}}
                ]
            }
        },
        {
            '$project': {
                'reservasInfo': {
                    '$filter': {
                        'input': '$reservasInfo',
                        'as': 'reserva',
                        'cond': {'$eq': ['$$reserva.revisada', False]}
                    }
                },
                'cumplioRutaInfoPasajeros': {
                    '$filter': {
                        'input': '$cumplioRutaInfoPasajeros',
                        'as': 'pasajero',
                        'cond': {'$eq': ['$$pasajero.revisada', False]}
                    }
                }
            }
        }
    ]

    rutas = collection.aggregate(pipeline)

    contexto = {'resenas': []}

    if rutas:
        for ruta in rutas:
            reservasInfo = ruta.get('reservasInfo', [])
            if reservasInfo:
                for reserva in reservasInfo:
                    resena_texto = reserva.get('reseña')
                    if resena_texto: 
                        contexto['resenas'].append({
                            'id': str(ruta['_id']),
                            'email': reserva.get('email'),
                            'resena': resena_texto,
                            'tipo': 'conductor'
                        })

            pasajerosInfo = ruta.get('cumplioRutaInfoPasajeros', [])
            if pasajerosInfo:
                for pasajero in pasajerosInfo:
                    resena_texto = pasajero.get('reseña')
                    if resena_texto:
                        contexto['resenas'].append({
                            'id': str(ruta['_id']),
                            'email': pasajero.get('email'),
                            'resena': resena_texto,
                            'tipo': 'pasajero'
                        })
    if usuario:
        contexto.update({
            'rol': usuario.get('rol'),
            'image_data': usuario.get('foto'),
            'usuario': usuario
        })

    return render(request, 'accounts/resena.html', contexto)





    



'''..............................................gestión de usuarios y administradores....................................................................'''

def eliminar_usuario(request, email):

    if not firebase_admin._apps:
        cred = credentials.Certificate('gouv2-b5056-firebase-adminsdk-mrmlq-7acc8fc2a8.json')
        firebase_admin.initialize_app(cred)
    
    try:
        user_record = auth.get_user_by_email(email)
        auth.delete_user(user_record.uid)

        usuarios_collection = db['Usuarios']
        invitados_collection = db['UsuarioInvitado']

        result_usuarios = usuarios_collection.delete_one({'email': email})
        result_invitados = invitados_collection.delete_one({'email': email})

        if result_usuarios.deleted_count > 0 or result_invitados.deleted_count > 0:
            messages.success(request, 'El usuario se eliminó correctamente de Firebase y MongoDB.')
        else:
            messages.warning(request, 'El usuario fue eliminado de Firebase, pero no se encontró en MongoDB.')

    except exceptions.FirebaseError as e:
        messages.error(request, f'Ocurrió un error al interactuar con Firebase: {e}')
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado al eliminar el usuario: {e}')

    return redirect('usuario')




def bloquear_usuario(request, email):
    if not firebase_admin._apps:
        cred = credentials.Certificate('gouv2-b5056-firebase-adminsdk-mrmlq-7acc8fc2a8.json')
        firebase_admin.initialize_app(cred)

    try:
        user_record = auth.get_user_by_email(email)

        usuarios_collection = db['Usuarios']
        invitados_collection = db['UsuarioInvitado']

        result_usuarios = usuarios_collection.update_one(
            {'email': email},
            {'$set': {'bloqueado': True}}
        )

        result_invitados = invitados_collection.update_one(
            {'email': email},
            {'$set': {'bloqueado': True}}
        )

        if result_usuarios.matched_count > 0 or result_invitados.matched_count > 0:
            messages.success(request, 'El usuario se bloqueó correctamente en MongoDB.')
        else:
            messages.warning(request, 'El usuario fue encontrado en Firebase, pero no se encontró en MongoDB.')

    except exceptions.FirebaseError as e:
        messages.error(request, f'Ocurrió un error al interactuar con Firebase: {e}')
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado al bloquear el usuario: {e}')

    return redirect('usuario')




def desbloquear_usuario(request, email):
    if not firebase_admin._apps:
        cred = credentials.Certificate('gouv2-b5056-firebase-adminsdk-mrmlq-7acc8fc2a8.json')
        firebase_admin.initialize_app(cred)

    try:
        user_record = auth.get_user_by_email(email)

        usuarios_collection = db['Usuarios']
        invitados_collection = db['UsuarioInvitado']

        result_usuarios = usuarios_collection.update_one(
            {'email': email},
            {'$set': {'bloqueado': False}}
        )

        result_invitados = invitados_collection.update_one(
            {'email': email},
            {'$set': {'bloqueado': False}}
        )

        if result_usuarios.matched_count > 0 or result_invitados.matched_count > 0:
            messages.success(request, 'El usuario se desbloqueó correctamente en MongoDB.')
        else:
            messages.warning(request, 'El usuario fue encontrado en Firebase, pero no se encontró en MongoDB.')

    except exceptions.FirebaseError as e:
        messages.error(request, f'Ocurrió un error al interactuar con Firebase: {e}')
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado al desbloquear el usuario: {e}')

    return redirect('usuario')



import firebase_admin
from firebase_admin import credentials, auth


def eliminar_admin(request, email):
    if not firebase_admin._apps:
        cred = credentials.Certificate('gou-adm-firebase-adminsdk-3hxpk-88999af45c.json')
        firebase_admin.initialize_app(cred)

    try:
        user_record = auth.get_user_by_email(email)
        auth.delete_user(user_record.uid)

        collection = db['GoUadmin']
        result = collection.delete_one({'correo': email})

        if result.deleted_count > 0:
            messages.success(request, 'El administrador se eliminó correctamente de Firebase y MongoDB.')
        else:
            messages.warning(request, 'El administrador fue eliminado de Firebase, pero no se encontró en MongoDB.')

    except exceptions.FirebaseError as e:
        messages.error(request, 'Ocurrió un error al interactuar con Firebase.')
    except Exception as e:
        messages.error(request, 'Ocurrió un error inesperado al eliminar el usuario.')

    return redirect('cuentas')


def bloquear_admin(request, email):
    if not firebase_admin._apps:
        cred = credentials.Certificate('gou-adm-firebase-adminsdk-3hxpk-88999af45c.json')
        firebase_admin.initialize_app(cred)

    try:
        user_record = auth.get_user_by_email(email)

        auth.update_user(user_record.uid, disabled=True)

        collection = db['GoUadmin']
        result = collection.update_one({'correo': email}, {'$set': {'bloqueado': True}})

        if result.matched_count > 0:
            messages.success(request, 'El administrador se bloqueó correctamente en Firebase y MongoDB.')
        else:
            messages.warning(request, 'El administrador fue bloqueado en Firebase, pero no se encontró en MongoDB.')

    except firebase_admin.exceptions.FirebaseError as e:
        messages.error(request, f'Ocurrió un error al interactuar con Firebase: {e}')
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado al bloquear el usuario: {e}')

    return redirect('cuentas')





def desbloquear_admin(request, email):
    if not firebase_admin._apps:
        cred = credentials.Certificate('gou-adm-firebase-adminsdk-3hxpk-88999af45c.json')
        firebase_admin.initialize_app(cred)

    try:
        user_record = auth.get_user_by_email(email)

        auth.update_user(user_record.uid, disabled=False)

        collection = db['GoUadmin']
        result = collection.update_one({'correo': email}, {'$set': {'bloqueado': False}})

        if result.matched_count > 0:
            messages.success(request, 'El administrador se desbloqueó correctamente en Firebase y MongoDB.')
        else:
            messages.warning(request, 'El administrador fue desbloqueado en Firebase, pero no se encontró en MongoDB.')

    except exceptions.FirebaseError as e:
        messages.error(request, f'Ocurrió un error al interactuar con Firebase: {e}')
    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado al desbloquear el administrador: {e}')

    return redirect('cuentas')



def crear_administrador(request):
    if request.method == 'POST':
        collection = db['GoUadmin']

        cred = credentials.Certificate("gou-adm-firebase-adminsdk-3hxpk-c216f44ec9.json")
        app = firebase_admin.initialize_app(cred, name='admin_app')

        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        rol = request.POST.get('rol')
        correo = request.POST.get('email')
        password = request.POST.get('password')
       

        try:
            with open('accounts/static/img/administra.jpg', 'rb') as image_file:
                default_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            administrador = {
                'nombre': nombre,
                'apellido': apellido,
                'rol': rol,
                'correo': correo,
                'foto': default_image_base64,
            }
            collection.insert_one(administrador)

            user = auth.create_user(
                app=app,
                email=correo,
                password=password
            )

            messages.success(request, '¡Administrador creado exitosamente!')
        except Exception as e:
            messages.error(request, f'Error al crear administrador: {str(e)}')
        finally:
            delete_app(app)

    return redirect('cuentas')



def aprobar_registro(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')

        try:
            object_id = ObjectId(registro_id)
        except Exception as e:
            messages.warning(request, 'Error en registro, no válido')

        collection_registros = db['RegistrosAutos']
        registro = collection_registros.find_one({'_id': object_id})

        if registro:
            collection_registros.update_one({'_id': object_id}, {'$set': {'RespuestaAprobacion': True}})
            messages.warning(request, 'Aprobación exitosa')
            return redirect('documento')
        else:
            messages.warning(request, 'Error en la aprobación')
    else:
        messages.warning(request, 'Error')
        return redirect('documento')



def rechazar_registro(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        motivo_rechazo = request.POST.get('motivo_rechazo', '')
        
        print(f"Registro ID recibido: {registro_id}")
        print(f"Motivo de rechazo recibido: {motivo_rechazo}")

        try:
            object_id = ObjectId(registro_id)
            print(f"Object ID generado correctamente: {object_id}")
        except Exception as e:
            print(f"Error al procesar el Object ID: {e}")
            messages.warning(request, 'Error al procesar el ID del registro.')
            return redirect('documento')

        collection_registros = db['RegistrosAutos']
        registro = collection_registros.find_one({'_id': object_id})
        print(f"Registro encontrado: {registro}")

        if registro:
            update_result = collection_registros.update_one(
                {'_id': object_id},
                {'$set': {'Rechazado': True, 'MotivoRechazo': motivo_rechazo}}
            )
            print(f"Resultado de la actualización: {update_result.modified_count} documento(s) actualizado(s)")

            try:
                email = registro.get('email')
                print(f"Email encontrado: {email}")

                if email:
                    send_mail(
                        'Notificación de Rechazo de Documento',
                        f'Le informamos que el documento que presentó ha sido rechazado. La razón de este rechazo es la siguiente: {motivo_rechazo}.\n\nSi tiene alguna pregunta o desea obtener más información sobre esta decisión, no dude en ponerse en contacto con nosotros.\n\nAtentamente,\n\nAdministradores GoU V2',
                        'gou2udec@gmail.com',
                        [email],
                        fail_silently=False,
                    )
                    print("Correo enviado exitosamente.")

                    messages.success(request, 'El documento ha sido rechazado y el motivo ha sido enviado por correo electrónico.')
                else:
                    print("Error: No se encontró un correo asignado en el registro.")
                    messages.error(request, 'No se pudo enviar el correo electrónico porque el registro no tiene un correo asignado.')
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
                messages.error(request, 'Error al enviar el correo electrónico.')

            return redirect('documento')
        else:
            print("Registro no encontrado.")
            messages.warning(request, 'Registro no encontrado.')
            return redirect('documento')
    else:
        print("Método no permitido.")
        messages.warning(request, 'Método no permitido.')
        return redirect('documento')



def gestion_costo_km(request):
    collection = db['Politi_Acuer_otros']

    if request.method == 'POST':
        nuevo_costo_km = float(request.POST.get('kilometro'))
        collection.update_one({}, {"$set": {"Costo_Km": nuevo_costo_km}})

        messages.success(request, 'El costo por kilómetro se ha actualizado exitosamente.')
        return redirect('documento')

    return render(request, 'accounts/gestion_costo_km.html')




def eliminar_resena(request, resena_id, tipo, email):
    collection = db['HistorialDeRutas']

    if tipo == 'conductor':
        result = collection.find_one(
            {'_id': ObjectId(resena_id), 'reservasInfo.email': email}
        )

        if result:
            collection.update_one(
                {'_id': ObjectId(resena_id)},
                {'$pull': {'reservasInfo': {'email': email}}}
            )

    elif tipo == 'pasajero':
        result = collection.find_one(
            {'_id': ObjectId(resena_id), 'cumplioRutaInfoPasajeros.email': email}
        )

        if result:
            collection.update_one(
                {'_id': ObjectId(resena_id)},
                {'$pull': {'cumplioRutaInfoPasajeros': {'email': email}}}
            )

    if email:
        send_mail(
            'Eliminación de Reseña por Infracción de Normas',
            'Le informamos que su reseña ha sido eliminada debido a una infracción de nuestras normas y políticas de uso. '
            'Nuestro equipo ha revisado su contenido y ha determinado que no cumple con los lineamientos establecidos para '
            'la publicación de reseñas en nuestra plataforma.\n\n'
            'Si considera que esta acción ha sido tomada por error o desea presentar una queja o reclamación, no dude en '
            'ponerse en contacto con nosotros a través de este correo: gou2udec@gmail.com. Estaremos encantados de revisar '
            'su caso y proporcionarle más detalles si es necesario.\n\n'
            'Atentamente,\n'
            'Administradores GoU V2',
            'gou2udec@gmail.com',
            [email],
            fail_silently=False,
        )

    return redirect('resena')



def advertir_resena(request, resena_id, tipo, email):
    collection = db['HistorialDeRutas']
    resena_id_obj = ObjectId(resena_id) 

    if tipo == 'conductor':
        collection.update_many(
            {
                '_id': resena_id_obj,
                'reservasInfo.email': email
            },  
            {'$set': {'reservasInfo.$[elem].revisada': True}},
            array_filters=[{'elem.email': email}]
        )

    elif tipo == 'pasajero':
        collection.update_many(
            {
                '_id': resena_id_obj,
                'cumplioRutaInfoPasajeros.email': email
            },  
            {'$set': {'cumplioRutaInfoPasajeros.$[elem].revisada': True}},
            array_filters=[{'elem.email': email}]
        )

    if email:
        send_mail(
            'Advertencia de Reseña',
            'Le informamos que su reseña ha sido revisada y se ha determinado que podría estar infringiendo nuestras normas y políticas de uso. '
            'Le pedimos que tenga precaución con las palabras y el contenido de sus reseñas para cumplir con los lineamientos establecidos en nuestra plataforma.\n\n'
            'Si tiene alguna pregunta o desea discutir esta advertencia, no dude en ponerse en contacto con nosotros a través de este correo: gou2udec@gmail.com.\n\n'
            'Atentamente,\n'
            'Administradores GoU V2',
            'gou2udec@gmail.com',
            [email],
            fail_silently=False,
        )

    return redirect('resena')


def marcar_revisada(request, resena_id, tipo, email):
    collection = db['HistorialDeRutas']
    resena_id_obj = ObjectId(resena_id) 

    if tipo == 'conductor':
        collection.update_many(
            {
                '_id': resena_id_obj,
                'reservasInfo.email': email
            },  
            {'$set': {'reservasInfo.$[elem].revisada': True}},
            array_filters=[{'elem.email': email}]
        )

    elif tipo == 'pasajero':
        collection.update_many(
            {
                '_id': resena_id_obj,
                'cumplioRutaInfoPasajeros.email': email
            },  
            {'$set': {'cumplioRutaInfoPasajeros.$[elem].revisada': True}},
            array_filters=[{'elem.email': email}]
        )

    return redirect('resena')

def reporte_rutas(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})

    if usuario:
        rol = usuario['rol']
        image_data = usuario['foto']
        return render(request, 'accounts/reporteRutas.html', {'rol': rol, 'image_data': image_data, 'usuario': usuario})
    return render(request, 'accounts/reporteRutas.html')
    


def buscar_ruta(request):
    email = request.GET.get('email')
    historial_rutas = db['HistorialDeRutas']
    historico_rutas = db['HistoricoDeRutas']

    if email:
        # Búsqueda insensible a mayúsculas/minúsculas
        ruta_data = historial_rutas.find_one({"email": re.compile(f"^{email}$", re.IGNORECASE)})
        historico_data = list(historico_rutas.find({"email": re.compile(f"^{email}$", re.IGNORECASE)}))
        
        if ruta_data:
            rutas = [{
                'nombre': ruta_data.get('nombre', ''),
                'apellidos': ruta_data.get('apellidos', ''),
                'email': ruta_data.get('email', ''),
                'origin': ruta_data['ruta']['origin'],
                'destination': ruta_data['ruta']['destination']
            }]

            # Filtrar la variable fechaSalida
            historial = [{
                'origin': hist.get('ruta', {}).get('origin', ''),
                'destination': hist.get('ruta', {}).get('destination', ''),
                # Filtrar la fechaSalida hasta que se encuentre una letra
                'fechaSalida': re.sub(r'[a-zA-Z].*', '', hist.get('fechaSalida', '')).strip(),
                'horaSalida': hist.get('horaSalida', '')
            } for hist in historico_data]
            
            return JsonResponse({'success': True, 'rutas': rutas, 'historial': historial})
        else:
            return JsonResponse({'success': False, })
    
    return JsonResponse({'success': False})

 
def agregar_pie_de_pagina(p, width, height):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.black)
 
    fecha_hora_text = f"Fecha y Hora de Generación: {fecha_hora}"
    fecha_hora_width = p.stringWidth(fecha_hora_text, "Helvetica-Oblique", 10)
    p.drawString((width - fecha_hora_width) / 2, 40, fecha_hora_text)
 
    firma = "Administradores de Gou II"
    firma_width = p.stringWidth(firma, "Helvetica-Oblique", 10)
    p.drawString((width - firma_width) / 2, 25, firma)
 
def draw_multiline_text(p, text, x, y, max_width, font_size=10):
    p.setFont("Helvetica", font_size)
    words = text.split(' ')
    current_line = ''
   
    for word in words:
        test_line = current_line + word + ' '
        line_width = p.stringWidth(test_line, "Helvetica", font_size)
 
        if line_width < max_width:
            current_line = test_line
        else:
            p.drawString(x, y, current_line)
            y -= font_size + 2
            current_line = word + ' '
 
    if current_line:
        p.drawString(x, y, current_line)
 
    return y
 
# Descargar pdf de usuarios UdeC
def descargar_historial_pdf(request):
    usuarios_collection = db['Usuarios']
   
    try:
        usuarios = list(usuarios_collection.find({}, {'_id': 1, 'nombre': 1, 'apellidos': 1, 'telefono': 1, 'email': 1, 'bloqueado': 1}))
       
        usuarios_not_blocked = [
            {
                'idusuario': str(user.get('_id')),
                'nombre': str(user.get('nombre')).title(),  # Convertir a cadena
                'apellidos': str(user.get('apellidos')).title(),  # Convertir a cadena
                'telefono': str(user.get('telefono')),  # Convertir a cadena
                'email': str(user.get('email'))  # Convertir a cadena
            }
            for user in usuarios if user.get('bloqueado') != True
        ]
 
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="usuarios_udec.pdf"'
 
        p = canvas.Canvas(response, pagesize=letter)
 
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.green)

        # Establecer metadatos del PDF
        p.setTitle("Reporte Usuarios UDEC")  # Cambia el título aquí
 
        width, height = letter
 
        titulo = "Historial de Usuarios UdeC"
        titulo_width = p.stringWidth(titulo, "Helvetica-Bold", 16)
        p.drawString((width - titulo_width) / 2, 750, titulo)
 
        p.setStrokeColor(colors.green)
        p.setLineWidth(2)
        p.line(50, 740, width - 50, 740)
 
        contexto_texto = (
            "En este reporte se visualizan los datos de los usuarios registrados y activos en la aplicación Gou V2, "
            "limitándose a aquellos que pertenecen a la Universidad de Cundinamarca, es decir, que sus correos "
            "electrónicos finalizan en @ucundinamarca.edu.co. Esta información es esencial para la gestión de "
            "la comunidad universitaria y asegura que se cumplan las normativas y requisitos de acceso a la aplicación."
        )
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y = 715
        max_width = width - 100
        y = draw_multiline_text(p, contexto_texto, 50, y, max_width)
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y -= 20
        espacio_entre_titulo_y_tabla = 20
        altura_cuadro = 70
 
        for user in usuarios_not_blocked:
            if y <= 100:
                agregar_pie_de_pagina(p, width, height)
                p.showPage()
                p.setFont("Helvetica", 12)
                y = 750
 
            p.setStrokeColor(colors.black)
            p.setLineWidth(1)
            p.rect(50, y - altura_cuadro, width - 100, altura_cuadro, fill=0)
 
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.green)
 
            p.drawString(60, y - 15, "ID:")
            p.drawString(60, y - 30, "Nombre:")
            p.drawString(60, y - 45, "Email:")
            p.drawString(60, y - 60, "Teléfono:")
 
            p.setFont("Helvetica", 12)
            p.setFillColor(colors.black)
 
            p.drawString(80, y - 15, user['idusuario'])
            p.drawString(115, y - 30, f"{user['nombre']} {user['apellidos']}")
            p.drawString(100, y - 45, user['email'])
            p.drawString(120, y - 60, user['telefono'])
           
            y -= (altura_cuadro + 10)
 
        agregar_pie_de_pagina(p, width, height)
 
        p.showPage()
        p.save()
 
        return response
 
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
 
# Descargar pdf de usuarios invitados
def descargar_invitados_pdf(request):
    invitados_collection = db['UsuarioInvitado']
   
    try:
        invitados = list(invitados_collection.find({}, {'_idusuario': 1, 'nombre': 1, 'apellidos': 1, 'telefono': 1, 'email': 1, 'bloqueado': 1}))
 
        invitados_not_blocked = [
            {
                'idusuario': str(guest.get('_idusuario')),  # Convertir a cadena
                'nombre': str(guest.get('nombre')).title(),  # Convertir a cadena
                'apellidos': str(guest.get('apellidos')).title(),  # Convertir a cadena
                'telefono': str(guest.get('telefono')),  # Convertir a cadena
                'email': str(guest.get('email'))  # Convertir a cadena
            }
            for guest in invitados if guest.get('bloqueado') != True
        ]
 
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invitados_udec.pdf"'
 
        p = canvas.Canvas(response, pagesize=letter)
 
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.green)
        
        # Establecer metadatos del PDF
        p.setTitle("Reporte Invitados UDEC")  # Cambia el título aquí

        width, height = letter
 
        titulo = "Historial de Invitados UdeC"
        titulo_width = p.stringWidth(titulo, "Helvetica-Bold", 16)
        p.drawString((width - titulo_width) / 2, 750, titulo)
 
        p.setStrokeColor(colors.green)
        p.setLineWidth(2)
        p.line(50, 740, width - 50, 740)
 
        contexto_texto = (
            "En este reporte se visualizan los datos de los invitados registrados y activos en la aplicación Gou V2, "
            "limitándose a aquellos que NO pertenecen a la Universidad de Cundinamarca. Esta información es esencial "
            "para la gestión de los usuarios y asegurar que se cumplan las normativas y requisitos "
            "de acceso a la aplicación."
        )
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y = 715
        max_width = width - 100
        y = draw_multiline_text(p, contexto_texto, 50, y, max_width)
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y -= 20
        espacio_entre_titulo_y_tabla = 20
        altura_cuadro = 70
 
        for guest in invitados_not_blocked:
            if y <= 100:
                agregar_pie_de_pagina(p, width, height)
                p.showPage()
                p.setFont("Helvetica", 12)
                y = 750
 
            p.setStrokeColor(colors.black)
            p.setLineWidth(1)
            p.rect(50, y - altura_cuadro, width - 100, altura_cuadro, fill=0)
 
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.green)
 
            p.drawString(60, y - 15, "ID:")
            p.drawString(60, y - 30, "Nombre:")
            p.drawString(60, y - 45, "Email:")
            p.drawString(60, y - 60, "Teléfono:")
 
            p.setFont("Helvetica", 12)
            p.setFillColor(colors.black)
 
            p.drawString(80, y - 15, guest['idusuario'])
            p.drawString(115, y - 30, f"{guest['nombre']} {guest['apellidos']}")
            p.drawString(100, y - 45, guest['email'])
            p.drawString(120, y - 60, guest['telefono'])
 
            y -= (altura_cuadro + 10)
 
        agregar_pie_de_pagina(p, width, height)
 
        p.showPage()
        p.save()
 
        return response
 
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
 
 
# Descargar pdf de usuarios bloqueados
def descargar_bloqueados_pdf(request):
    usuarios_collection = db['Usuarios']
   
    try:
        usuarios = list(usuarios_collection.find({}, {'_id': 1, 'nombre': 1, 'apellidos': 1, 'telefono': 1, 'email': 1, 'bloqueado': 1}))
       
        usuarios_blocked = [
            {
                'idusuario': str(user.get('_id')),
                'nombre': str(user.get('nombre')).title(),
                'apellidos': str(user.get('apellidos')).title(),  
                'telefono': str(user.get('telefono')),  
                'email': str(user.get('email'))  
            }
            for user in usuarios if user.get('bloqueado') == True
        ]
 
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="usuarios_bloqueados.pdf"'
 
        p = canvas.Canvas(response, pagesize=letter)
 
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.green)

        # Establecer metadatos del PDF
        p.setTitle("Reporte Bloqueados UDEC")  # Cambia el título aquí
       
        width, height = letter
 
        titulo = "Historial de Usuarios Bloqueados"
        titulo_width = p.stringWidth(titulo, "Helvetica-Bold", 16)
        p.drawString((width - titulo_width) / 2, 750, titulo)
 
        p.setStrokeColor(colors.green)
        p.setLineWidth(2)
        p.line(50, 740, width - 50, 740)
 
        contexto_texto = (
            "En este reporte se visualizan los datos de los usuarios que han sido bloqueados en la aplicación Gou V2. "
            "Esta información es esencial para la gestión de usuarios y asegura que se cumplan las normativas y "
            "requisitos de acceso a la aplicación."
        )
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y = 715
        max_width = width - 100
        y = draw_multiline_text(p, contexto_texto, 50, y, max_width)
 
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
 
        y -= 20
        espacio_entre_titulo_y_tabla = 20
        altura_cuadro = 70
 
        for user in usuarios_blocked:
            if y <= 100:
                agregar_pie_de_pagina(p, width, height)
                p.showPage()
                p.setFont("Helvetica", 12)
                y = 750
 
            p.setStrokeColor(colors.black)
            p.setLineWidth(1)
            p.rect(50, y - altura_cuadro, width - 100, altura_cuadro, fill=0)
 
            p.setFont("Helvetica-Bold", 12)
            p.setFillColor(colors.green)
 
            p.drawString(60, y - 15, "ID:")
            p.drawString(60, y - 30, "Nombre:")
            p.drawString(60, y - 45, "Email:")
            p.drawString(60, y - 60, "Teléfono:")
 
            p.setFont("Helvetica", 12)
            p.setFillColor(colors.black)
 
            p.drawString(80, y - 15, user['idusuario'])
            p.drawString(115, y - 30, f"{user['nombre']} {user['apellidos']}")
            p.drawString(100, y - 45, user['email'])
            p.drawString(120, y - 60, user['telefono'])
 
            y -= (altura_cuadro + 10)
 
        agregar_pie_de_pagina(p, width, height)
 
        p.showPage()
        p.save()
 
        return response
 
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
   
import tempfile
import os
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from django.http import HttpResponse
from datetime import datetime

def descargar_usu_desta(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Usuarios_Destacados.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Establecer metadatos del PDF
    p.setTitle("Reporte Usuarios Destacados")  # Cambia el título aquí
    
    width, height = letter

    # Titulo y estilos
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.green)
    titulo_text = "Usuarios Destacados"
    titulo_ancho = p.stringWidth(titulo_text, "Helvetica-Bold", 20)

    # Inicializa y a 300
    y = 750  # Ajustar la posición inicial para el título y el párrafo

    # Dibujar título en la primera página
    p.drawString((width - titulo_ancho) / 2, y, titulo_text)  # Centrar título
    p.setStrokeColor(colors.green)
    p.line(100, y - 5, 500, y - 5)  # Línea horizontal

    # Espacio entre la línea y el párrafo
    y -= 30  # Dejar espacio después de la línea

    p.setFont("Helvetica", 12)  # Tamaño de fuente
    p.setFillColor(colors.black)

    # Texto a insertar
    paragraph_text = (
        "En este reporte se visualizan a los usuarios con las mejores puntuaciones en la plataforma, "
        "este análisis busca resaltar el rendimiento y la satisfacción de los usuarios, brindando una "
        "perspectiva sobre la calidad del servicio ofrecido y fomentando una comunidad activa y comprometida. "
        "Los datos extraídos de la base de datos de usuarios destacados son: nombre completo, email, teléfono y calificación, "
        "este reporte incluye los detalles de los cinco usuarios con las calificaciones más altas, permitiendo "
        "una visualización clara y concisa de sus datos."
    )

    # Iniciar en Y
    y_text = y

    # Dividir el texto en líneas que quepan en la página
    lines = []
    words = paragraph_text.split(" ")
    current_line = ""

    for word in words:
        # Verificar si la línea actual más la nueva palabra cabe dentro del margen
        if p.stringWidth(current_line + " " + word, "Helvetica", 12) < (width - 100):
            current_line += " " + word
        else:
            # Si no cabe, guardar la línea actual y empezar una nueva
            lines.append(current_line)
            current_line = word  # Comenzar una nueva línea con la palabra actual

    # Añadir la última línea si no está vacía
    if current_line:
        lines.append(current_line)

    # Dibujar las líneas en el PDF
    for line in lines:
        p.drawString(50, y_text, line.strip())  # Usar 'strip' para eliminar espacios innecesarios
        y_text -= 15  # Ajustar el espacio entre líneas



    # Espacio reservado para el pie de página (mínimo 60 unidades en Y)
    margen_inferior = 30
    espacio_por_usuario = 150  # Altura que ocupa un usuario en el PDF (imagen + detalles)
    y -= 200  # Ajustar la posición Y para comenzar con los usuarios

    # Obtener los usuarios destacados de la base de datos
    usuarios_destacados = db['Usuarios'].find(
        {},
        sort=[('calificacionUser', -1)],
        projection={'_id': 0, 'imagen': 1, 'nombre': 1, 'apellidos': 1, 'email': 1, 'telefono': 1, 'calificacionUser': 1},
        limit=5
    )

    for usuario in usuarios_destacados:
        # Verificar si hay suficiente espacio en la página actual para dibujar el usuario
        if y - espacio_por_usuario < margen_inferior + 30:  # +60 para el pie de página
            agregar_pie_de_pagina(p, width, height)  # Agregar pie de página antes de cambiar de página
            p.showPage()  # Mover a la siguiente página
            y = 600  # Reiniciar la posición Y en la nueva página
            
            # Redibujar el título en la nueva página
            p.setFont("Helvetica-Bold", 20)
            p.setFillColor(colors.green)
            p.drawString((width - titulo_ancho) / 2, 750, titulo_text)  # Centrar título
            p.setStrokeColor(colors.green)
            p.line(100, 745, 500, 745)

        # Insertar los detalles del usuario al PDF
        if 'imagen' in usuario:
            # Decodificar la imagen del usuario desde Base64
            image_data = base64.b64decode(usuario['imagen'])
            # Crear un archivo temporal para guardar la imagen
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                tmp_img.write(image_data)
                temp_img_path = tmp_img.name  # Guardar la ruta de la imagen

            # Insertar la imagen en el PDF
            try:
                p.drawImage(temp_img_path, 100, y, width=100, height=100)
            except Exception as e:
                print(f"Error al insertar la imagen: {e}")

            # Eliminar el archivo temporal después de usarlo
            os.remove(temp_img_path)

        # Añadir los detalles del usuario al PDF
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
        # Convertir nombre y apellidos a título (primera letra en mayúscula)
        nombre_completo = f"● Nombre: {usuario['nombre'].title()} {usuario['apellidos'].title()}"
        p.drawString(220, y + 70, nombre_completo)
        p.drawString(220, y + 50, f"● Email: {usuario['email']}")
        p.drawString(220, y + 30, f"● Teléfono: {usuario.get('telefono', 'No disponible')}")
        p.drawString(220, y + 10, f"● Calificación: {usuario['calificacionUser']}")

        y -= espacio_por_usuario  # Ajustar la posición Y para el siguiente usuario

    # Reservar espacio para el pie de página y agregarlo
    agregar_pie_de_pagina(p, width, height)

    # Finalizar el PDF
    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response





def usuario_destacado(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})

    if usuario:
        rol = usuario['rol']
        image_data = usuario['foto']

        # Consulta para obtener los 5 usuarios con la mayor calificación
        usuarios_destacados = db['Usuarios'].find(
            {},
            sort=[('calificacionUser', -1)],
            projection={'_id': 0, 'imagen': 1, 'nombre': 1, 'apellidos': 1, 'email': 1, 'telefono': 1, 'calificacionUser': 1},
            limit=5  # Limitar a los 5 primeros usuarios
        )

        usuarios_lista = list(usuarios_destacados)  # Convertir el cursor a lista

        context = {
            'rol': rol,  
            'image_data': image_data,  
            'usuario': usuario,
            'usuarios_destacados': usuarios_lista  # Pasar la lista de usuarios destacados
        }

        return render(request, 'accounts/reporteUsuariosDestacados.html', context)
    
    return render(request, 'accounts/reporteUsuariosDestacados.html', {})

import io
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from django.http import HttpResponse
from collections import Counter
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

def descargar_municipios_pdf(request):
    # Obtener los datos de municipios del def reporte_municipio
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})
    
    if usuario:
        municipios_validos = [
            "Agua de Dios", "Albán", "Anapoima", "Arbeláez",
            "Beltrán", "Bituima", "Bogotá", "Bojacá",
            "Cabrera", "Cajicá", "Caparrapí", "Chocontá",
            "Chía", "Cota", "El Rosal", "Facatativá",
            "Fusagasugá", "Guasca", "Guatavita", "La Calera",
            "La Mesa", "La Peña", "Macheta", "Madrid",
            "Mosquera", "Nariño", "Nilo", "Pacho",
            "Paime", "Ricaurte", "San Antonio del Tequendama",
            "San Bernardo", "San Cayetano", "Sasaima", "Soacha",
            "Sopó", "Subachoque", "Tabio", "Tocancipá",
            "Ubalá", "Útica", "Venecia", "Zipaquirá"
        ]
        
        rutas = db['HistorialDeRutas'].find({}, {'ruta.origin': 1, 'ruta.destination': 1})
        origin_counter = Counter()
        destination_counter = Counter()

        municipios_validos_lower = [m.lower() for m in municipios_validos]

        for ruta in rutas:
            origin = ruta.get('ruta', {}).get('origin', '')
            destination = ruta.get('ruta', {}).get('destination', '')

            origin_lower = origin.lower()
            destination_lower = destination.lower()

            for municipio in municipios_validos_lower:
                if municipio in origin_lower:
                    municipio_original = municipios_validos[municipios_validos_lower.index(municipio)]
                    origin_counter[municipio_original] += 1

                if municipio in destination_lower:
                    municipio_original = municipios_validos[municipios_validos_lower.index(municipio)]
                    destination_counter[municipio_original] += 1
        
        # Obtener los top 5 resultados para ambos gráficos
        top_origin = origin_counter.most_common(5)
        top_destination = destination_counter.most_common(5)
        
        municipios_origin, counts_origin = zip(*top_origin) if top_origin else ([], [])
        municipios_destination, counts_destination = zip(*top_destination) if top_destination else ([], [])

        # Crear el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_municipios.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        # Cambiar el título del documento PDF (lo que aparece en la pestaña)
        p.setTitle("Reporte Municipios")

        width, height = letter
        
        # Título del reporte
        titulo_texto = "Reporte de Municipios - Origen y Destino"
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(colors.green)
        titulo_ancho = p.stringWidth(titulo_texto, "Helvetica-Bold", 20)
        p.drawString((width - titulo_ancho) / 2, height - 50, titulo_texto)

        # Línea verde horizontal debajo del título
        p.setStrokeColor(colors.green)
        p.setLineWidth(2)
        p.line(50, height - 60, width - 50, height - 60)

       # Espacio debajo de la línea horizontal
        p.setFont("Helvetica", 13)  # Tamaño de fuente
        p.setFillColor(colors.black)

        # Texto del párrafo
        texto_parrafo = (
            "Hemos recopilado una estadística que identifica los cinco municipios principales de origen de las rutas. "
            "Este informe permite al programa contabilizar cuántos municipios figuran en la variable de origen, "
            "lo que proporciona información valiosa sobre los puntos de inicio más frecuentes de los viajes. "
            "Asimismo, se genera otra gráfica que contabiliza los municipios de destino, lo que nos permite "
            "observar las áreas más comunes a las que los usuarios se dirigen. "
            "Este análisis detallado de las rutas nos ayuda a comprender mejor el comportamiento de nuestros usuarios."
        )

        # Función para dividir el texto en líneas
        def dividir_texto(p, texto, x, y, max_ancho):
            palabras = texto.split(' ')
            linea_actual = ''
            for palabra in palabras:
                # Comprobar si agregar la nueva palabra excede el ancho máximo
                if p.stringWidth(linea_actual + palabra, "Helvetica", 13) < max_ancho:
                    linea_actual += ' ' + palabra if linea_actual else palabra
                else:
                    # Dibujar la línea actual y comenzar una nueva línea
                    p.drawString(x, y, linea_actual)
                    y -= 15  # Espacio entre líneas
                    linea_actual = palabra  # Comenzar nueva línea con la nueva palabra
            # Dibujar cualquier texto que quede en la última línea
            if linea_actual:
                p.drawString(x, y, linea_actual)

        # Posicionar el texto
        max_ancho = width - 100  # Ancho máximo para el texto (márgenes de 50 en cada lado)
        text_y = height - 80  # Ajustar el espacio inicial
        dividir_texto(p, texto_parrafo, 50, text_y, max_ancho)




        # Verificar espacio disponible para el gráfico de origen
        espacio_necesario = 250 + 50  # 250 para el gráfico y 50 para el pie de página
        if text_y - espacio_necesario < 50:  # Si no hay espacio, iniciar nueva página
            p.showPage()
            p.setFont("Helvetica-Bold", 20)
            p.setFillColor(colors.green)
            p.drawString((width - titulo_ancho) / 2, height - 50, titulo_texto)
            p.setStrokeColor(colors.green)
            p.setLineWidth(2)
            p.line(50, height - 60, width - 50, height - 60)

            text_y = height - 80  # Reiniciar la posición vertical

        # Gráfico de barras para Origen
        plt.figure(figsize=(6, 4))
        plt.bar(municipios_origin, counts_origin, color='#add8e6')
        plt.xlabel("Municipios de Origen")
        plt.ylabel("Cantidad")
        plt.title("Top 5 Municipios de Origen")

        # Guardar el gráfico de origen en un buffer de imagen
        buffer_origin = io.BytesIO()
        plt.savefig(buffer_origin, format='png')
        plt.clf()
        buffer_origin.seek(0)
        image_origin = ImageReader(buffer_origin)
        

        # Dibujar gráfico de origen en el PDF
        p.drawImage(image_origin, 100, text_y - 450, width=400, height=250)  # Ajuste la posición

        # Actualizar el espacio disponible después de agregar el gráfico de origen
        text_y -= 450  # Restar la altura del gráfico

        # Verificar espacio para el gráfico de destino
        if text_y - espacio_necesario < 50:  # Si no hay espacio, iniciar nueva página
            p.showPage()
            p.setFont("Helvetica-Bold", 20)
            p.setFillColor(colors.green)
            p.drawString((width - titulo_ancho) / 2, height - 50, titulo_texto)
            p.setStrokeColor(colors.green)
            p.setLineWidth(2)
            p.line(50, height - 60, width - 50, height - 60)

            text_y = height - 80  # Reiniciar la posición vertical

        # Gráfico de barras para Destino
        plt.figure(figsize=(6, 4))
        plt.bar(municipios_destination, counts_destination, color='#90ee90')
        plt.xlabel("Municipios de Destino")
        plt.ylabel("Cantidad")
        plt.title("Top 5 Municipios de Destino")

        # Guardar el gráfico de destino en un buffer de imagen
        buffer_destination = io.BytesIO()
        plt.savefig(buffer_destination, format='png')
        buffer_destination.seek(0)
        image_destination = ImageReader(buffer_destination)

        # Dibujar gráfico de destino en el PDF
        p.drawImage(image_destination, 100, text_y - 250, width=400, height=250)  # Ajuste la posición

        # Agregar pie de página
        agregar_pie_de_pagina(p, width, height)

        # Finalizar y guardar el PDF
        p.showPage()
        p.save()

        return response

    # Si no hay usuario válido
    return HttpResponseRedirect('/some_error_page/')




 
def reporte_municipio(request):
    email = request.session.get('email')
    usuario = db['GoUadmin'].find_one({'correo': email})
 
    if usuario:
        rol = usuario['rol']
        image_data = usuario['foto']
       
        municipios_validos = [
            "Agua de Dios", "Albán", "Anapoima", "Arbeláez",
            "Beltrán", "Bituima", "Bogotá", "Bojacá",
            "Cabrera", "Cajicá", "Caparrapí", "Chocontá",
            "Chía", "Cota", "El Rosal", "Facatativá",
            "Fusagasugá", "Guasca", "Guatavita", "La Calera",
            "La Mesa", "La Peña", "Macheta", "Madrid",
            "Mosquera", "Nariño", "Nilo", "Pacho",
            "Paime", "Ricaurte", "San Antonio del Tequendama",
            "San Bernardo", "San Cayetano", "Sasaima", "Soacha",
            "Sopó", "Subachoque", "Tabio", "Tocancipá",
            "Ubalá", "Útica", "Venecia", "Zipaquirá"
        ]
       
        rutas = db['HistorialDeRutas'].find({}, {'ruta.origin': 1, 'ruta.destination': 1})
       
        origin_counter = Counter()
        destination_counter = Counter()
 
        municipios_validos_lower = [m.lower() for m in municipios_validos]
 
        for ruta in rutas:
            origin = ruta.get('ruta', {}).get('origin', '')
            destination = ruta.get('ruta', {}).get('destination', '')
 
            origin_lower = origin.lower()
            destination_lower = destination.lower()
 
            for municipio in municipios_validos_lower:
                if municipio in origin_lower:
                    municipio_original = municipios_validos[municipios_validos_lower.index(municipio)]
                    origin_counter[municipio_original] += 1
 
                if municipio in destination_lower:
                    municipio_original = municipios_validos[municipios_validos_lower.index(municipio)]
                    destination_counter[municipio_original] += 1
 
        top_origin = origin_counter.most_common(5)
        top_destination = destination_counter.most_common(5)
       
        municipios_origin, counts_origin = zip(*top_origin) if top_origin else ([], [])
        municipios_destination, counts_destination = zip(*top_destination) if top_destination else ([], [])
 
        return render(request, 'accounts/reporte_municipio.html', {
            'rol': rol,
            'image_data': image_data,
            'usuario': usuario,
            'municipios_origin': list(municipios_origin),
            'counts_origin': list(counts_origin),
            'municipios_destination': list(municipios_destination),
            'counts_destination': list(counts_destination),
        })
 
    return render(request, 'accounts/reporte_municipio.html', {})


# Función para formatear direcciones
def formatear_direccion(direccion):
    return direccion.replace(',', '\n').replace('#', '\n#')

# Función para formatear email (saltar línea al encontrar arroba o punto)
def formatear_email(email):
    return email.replace('@', '\n@').replace('.', '\n.')

# Función para formatear la fecha (quitar letras y todo lo que sigue después)
def formatear_fecha(fecha):
    return re.split(r'[a-zA-Z]', fecha)[0]

# Función para capitalizar cada palabra en nombre y apellidos
def capitalizar_palabras(texto):
    return ' '.join([palabra.capitalize() for palabra in texto.split()])

def generar_pdf_ruta(request):
    historial_rutas = db['HistorialDeRutas']
    historico_rutas = db['HistoricoDeRutas']
    
    email = request.GET.get('email')
    
    if email:
        ruta_data = historial_rutas.find_one({"email": re.compile(f"^{email}$", re.IGNORECASE)})
        historico_data = list(historico_rutas.find({"email": re.compile(f"^{email}$", re.IGNORECASE)}))

        if ruta_data:
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_ruta.pdf"'
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20)  # Ajusta el margen superior

            # Obtener estilos
            styles = getSampleStyleSheet()

            # Definir un estilo de subtítulo manualmente
            styles.add(ParagraphStyle(name='Subtitle', alignment=TA_LEFT, fontSize=12, spaceAfter=10))  # Alineado a la izquierda
            
            # Definir un estilo personalizado para los títulos en verde
            styles.add(ParagraphStyle(name='TitleGreen', alignment=TA_CENTER, fontSize=16, textColor=colors.green, fontName='Helvetica-Bold', spaceAfter=10))

            # Crear contenido
            content = []

            # Título principal (más cerca del margen superior)
            title = Paragraph("Reporte de Ruta", styles['TitleGreen'])
            content.append(title)
            
            # Línea verde debajo del título
            drawing = Drawing(500, 1)  # Definir el tamaño del dibujo
            line = Line(0, 0, 500, 0)  # Dibujar una línea de izquierda a derecha
            line.strokeColor = colors.green
            drawing.add(line)
            content.append(drawing)

            # Agregar un espacio debajo del título principal
            content.append(Spacer(1, 12))
            
            # Subtítulo actualizado alineado a la izquierda
            subtitle =  [
                "Este reporte está enfocado en presentar información relevante sobre la ruta actual que un conductor está realizando. Se utiliza para obtener una visión actualizada del trayecto en curso.",
                "Información presentada en el Reporte de Rutas:",
                "Correo electrónico: Identifica de manera única al conductor a través de su correo electrónico.",
                "Nombre completo: Se presentan tanto los nombres como los apellidos del conductor.",
                "Origen de la ruta: Indica el punto de partida del trayecto actual.",
                "Destino final de la ruta: Muestra el destino hacia el cual se dirige el conductor en ese momento."
            ]

            # Agregar cada línea del subtítulo con espacio entre ellas
            for line in subtitle:
                content.append(Paragraph(line, styles['Subtitle']))
                content.append(Spacer(1, 5))  # Añadir espaciado después de cada línea
                 
            data_personales = [
                ['Email', 'Nombres', 'Apellidos', 'Inicio de la Ruta', 'Destino Final'],
                [
                    formatear_email(ruta_data['email']),  # Aplicar formato al email
                    capitalizar_palabras(ruta_data.get('nombre', '')),  # Capitalizar cada palabra del nombre
                    capitalizar_palabras(ruta_data.get('apellidos', '')),  # Capitalizar cada palabra del apellido
                    formatear_direccion(ruta_data['ruta']['origin']), 
                    formatear_direccion(ruta_data['ruta']['destination'])
                ]
            ]

            table_personales = Table(data_personales, colWidths=[100, 80, 80, 100, 100])
            table_personales.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            content.append(table_personales)

            # Agregar un espacio (Spacer) después de la primera tabla
            content.append(Spacer(1, 25))  # Ajusta el valor del segundo parámetro para más o menos espacio

            # Historial (rutas anteriores del conductor)
            if historico_data:
                # Título de Historial de Rutas
                historial_title = Paragraph("Historial de Rutas", styles['TitleGreen'])
                content.append(historial_title)

                # Línea verde debajo del título de historial
                drawing2 = Drawing(500, 1)  # Definir el tamaño del dibujo
                line2 = Line(0, 0, 500, 0)  # Dibujar una línea de izquierda a derecha
                line2.strokeColor = colors.green
                drawing2.add(line2)
                content.append(drawing2)
                
                # Agregar un espacio debajo del título de historial
                content.append(Spacer(1, 12))

                # Agregar la descripción del historial de rutas
                historial_description_content = [
                    "Este reporte permite visualizar un registro completo de las rutas anteriores realizadas por un conductor. Está diseñado para brindar un historial detallado de los trayectos, lo cual es útil para analizar patrones de viaje o para proporcionar información histórica en caso de ser necesario.",
                    "Información presentada en el Reporte de Historial de Rutas:",
                    "Origen de la ruta: Se muestra el punto de partida del trayecto.",
                    "Destino de la ruta: Indica el punto final al cual llegó el conductor.",
                    "Fecha de salida: Incluye el día, mes y año en que la ruta fue realizada.",
                    "Hora de salida: Muestra la hora exacta en la que el conductor comenzó el viaje."
                ]

                # Agregar cada línea de la descripción del historial con espacio entre ellas
                for line in historial_description_content:
                    content.append(Paragraph(line, styles['Subtitle']))  # Alineado a la izquierda
                    content.append(Spacer(1, 5))  # Añadir espaciado después de cada línea

                data_historial = [['Origen', 'Destino', 'Fecha de Salida', 'Hora de Salida']]
                for hist in historico_data:
                    data_historial.append([
                        formatear_direccion(hist['ruta']['origin']),
                        formatear_direccion(hist['ruta']['destination']),
                        formatear_fecha(hist['fechaSalida']),  # Aplicar formato a la fecha
                        hist['horaSalida']
                    ])

                table_historial = Table(data_historial, colWidths=[100, 100, 80, 80])
                table_historial.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                content.append(table_historial)

            # Función para agregar pie de página a cada página
            def my_page(canvas, doc):
                width, height = letter  # Obtén el tamaño de la página
                canvas.setTitle("Reporte Conductor")  # Cambia el título aquí
                agregar_pie_de_pagina(canvas, width, height)

            doc.build(content, onFirstPage=my_page, onLaterPages=my_page)
            
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        else:
            return JsonResponse({'success': False, 'message': 'El correo no existe en la base de datos'})
    
    return JsonResponse({'success': False, 'message': 'Correo no proporcionado'})

