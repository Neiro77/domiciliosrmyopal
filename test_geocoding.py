import requests

OPENCAGE_API_KEY_TEST = 'b76a29b5b1fe4a11be70d81a9e901bf2' # Tu clave
direccion_test = "Calle 15 14-35, Bogota, Colombia" # Una dirección de prueba

base_url = "https://api.opencagedata.com/geocode/v1/json"
params = {
    "q": direccion_test,
    "key": OPENCAGE_API_KEY_TEST,
    "language": "es",
    "no_annotations": 1
}

try:
    response = requests.get(base_url, params=params)
    response.raise_for_status() # Lanza un error para respuestas HTTP malas (4xx o 5xx)
    data = response.json()

    if data and data['results']:
        lat = data['results'][0]['geometry']['lat']
        lng = data['results'][0]['geometry']['lng']
        print(f"Geocodificación Exitosa para '{direccion_test}': Lat={lat}, Lng={lng}")
    else:
        print(f"No se encontraron coordenadas para la dirección: '{direccion_test}'")
        print(f"Respuesta completa de la API: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error al geocodificar dirección: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Respuesta de la API (código {e.response.status_code}): {e.response.text}")