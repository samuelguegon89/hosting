#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import MySQLdb
import os

dominio = sys.argv[1]

usuario = dominio.split('.')[0]

#Comprobamos que el dominio existe
conn = MySQLdb.connect(host="localhost",user="proftpd",passwd="proftpd",db="ftpd")
cursor = conn.cursor()
consulta = 'select username from usuarios where dominio = "%s";' % dominio
resultado = cursor.execute(consulta)
cursor.close()
conn.close()

if resultado == 0:
	print "El dominio no existe"
else:
	#Desactivamos el virtualhost
	os.system("a2dissite "+dominio+" 1>/dev/null 2>/dev/null")
	#Desactivamos el virtualhost para mysql
	os.system("a2dissite mysql_"+usuario+" 1>/dev/null 2>/dev/null")
	#Borramos los archivos de los virtualhosts
	os.system("rm /etc/apache2/sites-available/mysql_"+usuario)
	os.system("rm /etc/apache2/sites-available/"+dominio)
	#Borramos el directorio personal del usuario
	os.system("rm -R /srv/www/"+usuario)

	#Eliminamos el usuario mysql y la base de datos
	conn = MySQLdb.connect(host="localhost",user="root",passwd="root")
	cursor = conn.cursor()
	consulta = "drop database my%s" % usuario
	cursor.execute(consulta)
	conn.commit()
	consulta = "drop user my%s@localhost" % usuario
	cursor.execute(consulta)
	conn.commit()
	conn.close()
	
	#Eliminamos el usuario de ftpd
	conn = MySQLdb.connect(host="localhost",user="root",passwd="root",db="ftpd")
	cursor = conn.cursor()
	consulta = "delete from usuarios where username = '%s';" % usuario
	cursor.execute(consulta)
	conn.commit()
	conn.close()

	#Eliminamos la zona DNS 
	os.system("rm -R /var/cache/bind/db."+dominio)
	archivo = open("/etc/bind/named.conf.local","r")
	lista = archivo.readlines()
	archivo.close()
	numero_linea = lista.index('zone "%s" { \n' % dominio)
	numero_linea_final = int(numero_linea) + 4
	os.system("sed -i '%s,%sd' /etc/bind/named.conf.local" % (numero_linea,numero_linea_final))

	print "El usuario %s y el dominio %s han sido eliminados correctamente" %(usuario,dominio)

	#Reiniciamos los servicios
	os.system("service apache2 restart 1>/dev/null 2>/dev/null")
	os.system("service bind9 restart 1>/dev/null 2>/dev/null")
	os.system("service proftpd restart 1>/dev/null 2>/dev/null")
