#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# copyleft © 2013 Facundo M. Acevedo <Acv2Facundo [Arrboa] gmail [punto] com>
#
# Distributed under terms of the BOLA license.

"""
Limpia la cola de mailq segun se lo requiera
"""

global msg_opcionInvalida, logger, DEBUG, MAILQ, RUTA_MAILS
#CONFIGRACION
MAILQ="/usr/bin/mailq"
#RUTA_MAILS="/var/spool/mqueue/"
RUTA_MAILS="/var/spool/postfix/active/"
DEBUG = True


#http://docs.python.org/2/howto/argparse.html#id1
import argparse
import subprocess
import logging
import os
import sys


logging.basicConfig(filename="/tmp/spampy.log", level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p' )
logger = logging.getLogger("SpamPy")

msg_combinacionInvalida = "La combinacion de opciones es invalida, verifique el modo de uso"
msg_opcionInvalida = "Verifique los parametros ingresados"

def main():
    logger.info("--Iniciando")
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",required=False,
                        help="Muestra un poco mas de info", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--correo", type=str,
                        help="Correo usado como filtro", required=False)
    group.add_argument("-f", "--borrarTodo", required=False,
                        help="Borra toda la cola del mailq", action="store_true")

    group.add_argument("-s", "--spam",required=False,
                        help="Lista los id de correo spam", action="store_true")



    args = parser.parse_args()

    if args.verbose:
        DEBUGE = True

    if args.correo:
        if DEBUG: print "Filtrando por correo"
        correo = args.correo
        logger.info("Filtro por correo "+str(correo))
        filtrarPorEmail(correo)

    elif args.borrarTodo:
        if DEBUG: print "Borrar todo"
        logger.info("Borro completamente la cola")
        borrarTodo()

    elif args.spam:
        if DEBUG: print "Filtrando spam"
        logger.info("Filtro spam.")
        filtrarSpam()

    else:
       parser.print_help()

    salir("")



def salir(msg=""):
    logger.info("--Fin\n")
    if msg:
        print msg
    exit(0)

def obtenerColaMailq():
    "Obtiene la cola de mails"
    if DEBUG: print sys._getframe().f_code.co_name

    #corro el proceso
    proceso = subprocess.Popen(MAILQ, stdout=subprocess.PIPE)
    # Me devuelve una tupla
    salida = proceso.communicate()

    return salida[0]


def procesarSalidaMailq(texto):
    """Procesa la entrada de texto, y saca un diccionario donde las llaves son el
    idDelMail y el valor [remitente, destinatario]"""
    if DEBUG: print sys._getframe().f_code.co_name
    salida = {} #Esta sera la salida
    idCorreo = ""
    #Corto por renglones
    renglones = texto.split("\n")

    #Busco algo asi -> 3hp5vw46BTzKpsC*      5964 Wed Sep  3 10:43:40 mzlocutora@hotmail.com
    #Recorro los renglones y parseo
    for renglon in renglones:
        listaComponentes = renglon.split()
        #Compruebo que haya remitente/detinatario
        #if (renglon.find("<") != -1) and (renglon.find(">") != -1) and  (renglon.find("(Deferred:") == -1):
        if ( len(listaComponentes) == 7 and validarEmail(listaComponentes[-1]) ):
            #Algunas versiones de mailq le agregan un asterisco al id
            idCorreo = listaComponentes[0].replace("*","")
            print idCorreo
            print listaComponentes
            #Verifico que sea la linea que tiene el id del mail
            if len(listaComponentes) == 7:
                salida[idCorreo] = [quitarMenorMayor(listaComponentes[6])]

            else:
                #En este caso voy guardando los destinatarios
                salida[idCorreo].append(quitarMenorMayor(renglon))

    return salida

def filtrar(diccionario, email="", spam = False):
    """Filtra por email o spam, sin filtros, devuelve una lista vacia"""
    if DEBUG: print sys._getframe().f_code.co_name
    listadoId = []
    if validarEmail(email) and spam == False:
        for _id in diccionario.keys():
            remitente = diccionario[_id][0]
            if remitente == email:
                listadoId.append(_id)
        return listadoId

    elif  spam == True:
        for _id in diccionario.keys():
            remitente = diccionario[_id][0]
            if remitente == "":
                listadoId.append(_id)
        return listadoId

    else:
        return []

def guardarInforme(listadoId, mensaje):
    logger.info(mensaje)
    logger.info(repr(listadoId))

def filtrarPorEmail(mail):
    if DEBUG: print sys._getframe().f_code.co_name
    colaSinProcesar = obtenerColaMailq()
    colaProcesada = procesarSalidaMailq(colaSinProcesar)
    idsFiltrados = filtrar(colaProcesada, email=mail)
    if len(idsFiltrados) <= 0:
        guardarInforme([], "No se encontro ningun correo con "+str(mail)+" como remitente")
        print "No hay mails con ese remitente"
        return

    guardarInforme(idsFiltrados, "Se encontraron estos correos con "+str(mail)+" como remitente:")
    presentarListaid("Id de los correos:",idsFiltrados)
    borrar(idsFiltrados, forzado=False)

def filtrarSpam():
    if DEBUG: print sys._getframe().f_code.co_name
    colaSinProcesar = obtenerColaMailq()
    colaProcesada = procesarSalidaMailq(colaSinProcesar)
    idsFiltrados = filtrar(colaProcesada,spam=True)
    if len(idsFiltrados) <= 0:
        guardarInforme([], "No hay spam :D")
        print "Genial! no hay spam :D"
        return

    guardarInforme(idsFiltrados, "Se encontraron estos id que son spam:")
    presentarListaid("Id del spam:",idsFiltrados)
    borrar(idsFiltrados, forzado=False)

def borrarTodo():
    borrar("BorrarTodo")

def borrar(ids, forzado = False):
    """Borra los mails segun el id recibido"""
    if DEBUG: print sys._getframe().f_code.co_name
    archivosEnDirectorio = []

    if ids == "BorrarTodo":
        for archivo in os.listdir(RUTA_MAILS):
            #dentro del nombre del archivo esta el id que queremos borrar
            ruta = os.path.join(RUTA_MAILS, archivo)
            try:
                if os.path.isfile(ruta):
                    logger.info("Borrando: "+str(ruta))
                    os.unlink(ruta)

            except Exception ,e:
                print e
                logger.info("Error: "+ str(e))

    #Busco los archivos
    if not forzado:
        rta = raw_input("¿Estas seguro de borrar esos mails? ")
        if rta.lower() in ["si", "yes", "s", "y"]:
            print "Borrando..."
            pass
        else:
            print "Nada fue borrado"
            salir()


    for archivo in os.listdir(RUTA_MAILS):
        for _id in ids:
            if archivo.find(_id) != -1:
                #dentro del nombre del archivo esta el id que queremos borrar
                ruta = os.path.join(RUTA_MAILS, archivo)
                try:
                    if os.path.isfile(ruta):
                        logger.info("Borrando: "+str(ruta))
                        os.unlink(ruta)

                except Exception ,e:
                    print e
                    logger.info("Error: "+ str(e))


def presentarListaid(titulo,lista):
    lista_= []
    m=4 # cantidad maxima de columnas
    a=0 #auxiliar
    b=0
    print"\n"+str(titulo)
    for elemento in lista:
            if a==m:
                a=0
                b=b+1
                print ' | '.join('{0}'.format(x) for x in lista_)
                lista_= []
            lista_.append(elemento)
            a=a+1
    #Parche mugroso para cuando hay menos de 4 elementos en la lista
    if b == 0:
            print ' | '.join('{0}'.format(x) for x in lista_)

def quitarMenorMayor(linea):
    return linea.replace("<", "").replace(">", "")

def validarEmail(direccion):
    if direccion.find("@") > 0 and direccion.find(".") > 0:
        return True
    return False


main()
