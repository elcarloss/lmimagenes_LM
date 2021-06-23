#!/usr/bin/python

import xml.etree.ElementTree as ET
from flask import Flask
from flask import request
import geopy.distance
import geojson
from geojson import Feature, Point, FeatureCollection
import json
from json import dumps
from waitress import serve
import operator
import arrow

def validarpunto(puntos):
    if (puntos[0] > 200 or puntos[1] > 200):
        puntos = (0,0)
    else:
        if (puntos[0] < 0):
            puntos = (puntos[1], puntos[0])
        if puntos[1] > 0:
            puntos = (puntos[0], '-' + str(puntos[1]))
            puntos = (puntos[0], float(puntos[1]))
        if (puntos[0] > 0 and puntos[1] > 0):
            puntos = (puntos[1], puntos[0])
    return puntos

class Gasolina_lugares:
    def __init__(self, doc, latitud, longitud, distancia):
        self.lista_places = []
        datos = []
        cont = 0
        cont2 = 0
        con = 1
        x = 0
        cont_punto = 1
        cont_ide = 0
        usuario = str(latitud)+','+str(longitud)
        tree_places  = ET.parse(doc)
        root_places = tree_places.getroot()
        lat = latitud
        lon = longitud
        for child in root_places:
            ide = child.attrib['place_id']
            for nietos in child:
                cont = cont + 1
                if nietos.tag == 'name':
                    nombre = nietos.text
                if nietos.tag == "location":
                    x = 0
                    for element in nietos:
                        x = x + 1
                        if x == 2:
                            lon = element.text
                        if x == 1:
                            lat = element.text
                    tup = (float(lon), float(lat))
                    tupgeopy = validarpunto(tup)
                    if ((geopy.distance.distance(usuario, tupgeopy).m) <= int(distancia)):
                        tupgeopyexp = (tupgeopy[1], tupgeopy[0])
                        lista_temporal = [ide, nombre, tupgeopyexp]
                        self.lista_places.append(lista_temporal)

        def __call__(self, *args, **kwargs):
            return self.lista_places

class Gasolina_precios:
    def __init__(self, doc, lista_places):
        self.lista_dict = []
        geometry = []
        props = []
        imagen = 'icogas.png'
        listamypoint = []
        featurecollection = []
        listafeat=[]
        datos = []
        nombre = ''
        cont_vueltas = 1
        icoverde = {"image" : "icogasverde.png"}
        icorojo = {"image" : "icogasrojo.png"}
        treeprices = ET.parse(doc)
        rootprices = treeprices.getroot()

        for id in lista_places:
            cont_vueltas = 1
            encontrados = rootprices.findall("./place/[@place_id='%s']" % id[0])
            if cont_vueltas < 3:
                for prices in encontrados:
                    precios = []
                    if (len(encontrados) > 1 and cont_vueltas <= 3):
#                        print("Entro al len encontrados")
                        for vuelta in range(len(encontrados)):
                            for datos in encontrados[vuelta]:
                                precios.append(datos.get('type'))
                                precios.append(datos.text)
                                cont_vueltas += 1
                        mypoint = Point(id[2])
                    else:
                        for prices in encontrados:
                            for datos in prices:
                                precios.append(datos.get('type'))
                                precios.append(datos.text)
                        mypoint = Point(id[2])
                                #                        precios.append(datos.get('update_time'))
#                print("Point id[2]: ",Point(id[2]))
#                print("Precios :", precios)
                if precios[0] == "regular":
                    if  len(precios) == 6:
                        propiedades = {'description':  precios[0]+': '+precios[1]+', '+precios[2]+': '+precios[3]+', '+precios[4]+': '+precios[5]+' - ID '+id[0], 'title' : id[1], 'image': imagen, 'point' : mypoint}
                    else:
                        if len(precios) == 4:
                            propiedades = {'description':  precios[0]+': '+precios[1]+', '+precios[2]+': '+precios[3]+', - ID '+id[0], 'title' : id[1], 'image': imagen, 'point' : mypoint}
                        else:
                            if len(precios) == 2:
                                propiedades = {'description':  precios[0]+': '+precios[1]+', - ID '+id[0], 'title' : id[1], 'image': imagen, 'point' : mypoint}
                    self.lista_dict.append(propiedades)
                else:
                    if (len(precios) == 6 and precios[4] == "regular"):
                        propiedades = {'description':  precios[4]+': '+precios[5]+', '+precios[2]+': '+precios[3]+', '+precios[0]+': '+precios[1]+' - ID '+id[0], 'title' : id[1], 'image': imagen, 'point' : mypoint}
                    else:
                        if (len(precios) == 4 and precios[2] == "regular"):
                            propiedades = {'description':  precios[2]+': '+precios[3]+', '+precios[0]+': '+precios[1]+', - ID '+id[0], 'title' : id[1], 'image': imagen, 'point' : mypoint}
                    self.lista_dict.append(propiedades)
        self.lista_dict.sort(key=operator.itemgetter('description'))
#        print("Lista Ordenada: ",self.lista_dict)

        def __call__(self, *args, **kwargs):
            return self.lista_dict

class Gasolina_Archivo:
    def genera_archivo(listadict, time_stamp):
#Genera el archivo de propiedades para enviar de regreso a la aplicación
        lista_dict = listadict
        featurecollection = []
        cont2 = 0
        con = 1
        icoverde = {"image" : "icogasverde.png"}
        icorojo = {"image" : "icogasrojo.png"}
        for x in lista_dict:
            puntos = x['point']
#            print("Puntos: ", puntos)
            x.pop('point')
            cadaux = lista_dict[cont2]['description']
            if (listadict[cont2]['description'][0] != 'd' and listadict[cont2]['description'][0] != 'p' and con == 1):
#                print("ENTRO GASOLINA BARATA!!!!!!!!!")
                lista_dict[cont2].update(icoverde)
                con = 2
            print("Cont2: ", cont2)
            if 'regular' in lista_dict[cont2]['description'] and len(listadict) == (cont2+1):
#                print("ENTRO A LA GASOLINA MAS CARA!!!!")
                lista_dict[cont2].update(icorojo)
            feature = Feature(geometry=puntos, properties=x)
            featurecollection.append(feature)
            cont2 += 1
        geojson_file = FeatureCollection(featurecollection)
#        print("Escribiendo archivo")
        archivo = "/var/www/html/"+str(time_stamp)+".json"
        f=open(archivo,'w')
        json.dump(geojson_file, f)
        f.close()

app = Flask(__name__)

@app.route('/puntos')
def puntos():
    lati = request.args.get('params1', 'no contiene este parametro')
    lon = request.args.get('params2', 'no contiene este parametro')
    km = request.args.get('params3', 'no contiene este parametro')
    time_stamp = request.args.get('params4', 'no contiene este parametro')
    usuario = str(lati+','+lon)
    places = Gasolina_lugares("/home/ubuntu/preciosgasolina/places", latitud=lati, longitud=lon, distancia=km)
    precios = Gasolina_precios("/home/ubuntu/preciosgasolina/prices", places.lista_places)
    archivo = Gasolina_Archivo.genera_archivo(precios.lista_dict, time_stamp)
    salida = "Archivo escrito correctamente"
    return "salida"

if __name__ == '__main__':
    #app.run(host='192.168.15.10', debug = True, port=3080)
    serve(app, host='70.37.160.249', port=3080)
