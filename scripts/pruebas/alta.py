#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import MySQLdb
import os
import string
from random import choice

#Función contraseñas aleatorias
def GenPasswd(n):
	return ''.join([choice(string.letters + string.digits) for i in range(n)])


usuario = sys.argv[1]
dominio = sys.argv[2]

#Conexion BBDD
conn = MySQLdb.connect(host="localhost",user="proftpd",passwd="proftpd",db="ftpd")

cursor = conn.cursor()

consulta = 'select username from usuarios where username = "%s";' % usuario

resultado = cursor.execute(consulta)

#Resultado devuelve 1 ó 0 dependiendo de si hay coincidencia
if resultado != 0:
	print "El usuario %s ya existe, intentelo de nuevo" % usuario
else:
	#comprobamos si existe el dominio
	consulta = 'select dominio from usuarios where dominio = "%s";' % dominio
	resultado = cursor.execute(consulta)

	if resultado != 0:
		print "El dominio %s ya existe, intentelo de nuevo" % dominio
	else:

		#VIRTUALHOST
		os.system('mkdir /srv/www/%s' % usuario)
		#os.system('cp /var/www/index.html /srv/www/%s' % usuario)
		plantilla = open('/srv/plantillas/index.html','r')
		lectura = plantilla.read()
		plantilla.close()
		lectura = lectura.replace("***usuario***",usuario)
		os.system('touch /srv/www/%s/index.html' % usuario)
		index = open('/srv/www/%s/index.html' % usuario,'w')
		index.write(lectura)
		index.close()

		plantilla = open('/srv/plantillas/vhost','r')
		lectura = plantilla.read()
		plantilla.close()

		#Creamos y abrimos el virtualhost en modo escritura
		os.system('touch /etc/apache2/sites-available/%s' % dominio)
		vhost = open('/etc/apache2/sites-available/'+dominio,'w')

		#Reemplazamos en el contenido el usuario y el dominio
		lectura = lectura.replace("//usuario//",usuario) 
		lectura = lectura.replace("//dominio//",dominio) 
		vhost.write(lectura)
		vhost.close()

		#Activamos el nuevo virtual host
		os.system("a2ensite "+dominio+" 1>/dev/null 2>/dev/null")

		#DNS
		p_zonas = open('/srv/plantillas/p_zonas','r')
		lectura = p_zonas.read()
		p_zonas.close()
		lectura = lectura.replace("//dominio//",dominio)
		zonas = open('/etc/bind/named.conf.local','a')
		zonas.write('\n'+lectura)
		zonas.close()

		#Abrimos la plantilla de definicion de las zonas y metemos su contenido en una variable
		p_defzona = open('/srv/plantillas/p_defzona','r')
		lectura = p_defzona.read()
		p_defzona.close()
		lectura = lectura.replace("//dominio//",dominio)
		os.system('touch /var/cache/bind/db.'+dominio)
		dzona = open('/var/cache/bind/db.'+dominio,'w')
		dzona.write(lectura)
		dzona.close()


		#Contraseñas para ftp y mysql
		contra_ftp = GenPasswd(7)
		contra_mysql = GenPasswd(7)

		#FTP
		#Buscamos el uid maximo
		consulta = "select max(uid) from usuarios;"
		cursor.execute(consulta)
		#Obtenemos un elemento del cursor
		uidmax = cursor.fetchone()
		if uidmax[0] == None:
			uid = "2100"
		else:
			uid = str(int(uidmax[0])+1)

		consulta = "insert into usuarios values ('"+usuario+"',password('"+contra_ftp+"'),"+uid+",2005,'/srv/ftp/"+usuario+"','/bin/bash',1,'"+dominio+"');"
		
		cursor.execute(consulta)
		conn.commit()
		
		cursor.close()
		conn.close()
		os.system('mkdir /srv/ftp/'+usuario)
		os.system('chown -R '+uid+':www-data /srv/ftp/'+usuario)
		os.system('chmod -R 770 /srv/ftp/'+usuario)
		print " "
		print "*****Anote su nombre de usuario y contraseña para FTP*****"
		print "Usuario------- %s" % usuario
		print "Contraseña---- %s" % contra_ftp
		print " "

		#PHPMYADMIN
		#Abrimos nueva conexión a la base de datos
		conn = MySQLdb.connect(host="localhost",user="root",passwd="root")
		cursor = conn.cursor()
		consulta = "create database my"+usuario
		cursor.execute(consulta)
		conn.commit()

		consulta = "grant all on my"+usuario+".* to my"+usuario+"@localhost identified by '"+contra_mysql+"';"
		cursor.execute(consulta)
		conn.commit()
		cursor.close()
		conn.close()
		print "*****Anote su nombre de usuario y contraseña para MYSQL*****"
		print "Usuario------- my"+usuario
		print "Contraseña---- "+contra_mysql
		print " "

		#Creamos el virtualhost del usuario para acceder a phpmyadmin
		plantilla = open('/srv/plantillas/mysqlhost','r')
		lectura = plantilla.read()
		plantilla.close()

		#Creamos y abrimos el virtualhost en modo escritura
		os.system('touch /etc/apache2/sites-available/mysql_%s' % usuario)
		mysql_host = open('/etc/apache2/sites-available/mysql_'+usuario,'w')

		lectura = lectura.replace("//usuario//",usuario) 
		lectura = lectura.replace("//dominio//",dominio) 
		mysql_host.write(lectura)
		mysql_host.close()

		#Activamos el nuevo virtual host
		os.system("a2ensite mysql_"+usuario+" 1>/dev/null 2>/dev/null")

		print "El usuario %s y el dominio %s han sido creados satisfactoriamente" %(usuario,dominio)
		print " "

		#Reiniciamos servicios
		os.system("service apache2 restart 1>/dev/null 2>/dev/null")
		os.system("service bind9 restart 1>/dev/null 2>/dev/null")
		os.system("service proftpd restart 1>/dev/null 2>/dev/null")
