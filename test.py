#!/usr/bin/python

import getopt, os, sys, time
import MySQLdb as mdb

from subprocess import *

#fonction qui sert a executer des commande linux
def run_cmd(cmd):
        p = Popen(cmd, shell=True, stdout=PIPE)
        output = p.communicate()[0]
        return output

def addslashes(s):
    l = ["\\", '"', "'", "\0", ]
    for i in l:
        if i in s:
            s = s.replace(i, '\\'+i)
    return s

#fonction pour trouver le typage de la variable
def is_array(degisken,tip):
   return isinstance(degisken,tip)


#installer d'abord mysql pour python => sudo apt-get install python-mysqldb
#configurations mysql
tmp_root="root"
tmp_mdp="team"
tmp_host="localhost"
tmp_bd="test"

EXCLUDE_FILE='/home/pauligno/script/exclude.txt'
SSH_PORT=22

def upload(user,serveur,mode,local,distant):
	# recuperer les access en mysql pour la connexion ssh
	con = None
	try:
		#connexion
		con = mdb.connect(tmp_host, tmp_root, tmp_mdp, tmp_bd);
		#definit que le curseur qui permet les cles associatives
		cur = con.cursor(mdb.cursors.DictCursor)

                #recuperer info user
                cur.execute("SELECT * FROM t_user WHERE nom='"+user+"' ")
                rows = cur.fetchall()
		#securite
        	if len(rows)==0:
		        error = "Error user %s: non trouve" % (user)
		        print error
		        sys.exit(1)

                for row in rows:
			workspace = row["workspace"]
			#print workspace
	
                #recuperer info serveur
		if mode=="dev":
			tmp_type=0
		if mode=="prod":
			tmp_type=1
		cur.execute("SELECT * FROM table_portail WHERE code='"+serveur+"' AND type='"+str(tmp_type)+"' ")
                rows = cur.fetchall()
		#securite
        	if len(rows)==0:
		        error = "Error portail %s type %s: non trouve" % (serveur,mode)
		        print error
		        sys.exit(1)

		for row in rows:
			user_serveur = row["user"]
			domaine_serveur = row["serveur"]
			racine_serveur = row["racine"]
			dossier_local = row["dossier_local"]
			exception_rsync = row["exception"]
			

                #preparer la commande rsync
		rsync_cmd = "rsync -avu --no-p --no-g --chmod=ugo=rwX --stats --progress --ignore-errors --exclude-from=%s %s --recursive " % (EXCLUDE_FILE, exception_rsync)
		
		dir_online = "%s@%s:%s" % (user_serveur, domaine_serveur,racine_serveur)
		if distant!="./":
			dir_online += distant
		dir_local = "%s%s" % (workspace,dossier_local)
		if local!="./":	
			dir_local += local
		
		rsync_cmd += " -e ssh -p %s \"%s\" \"%s\" " % (SSH_PORT, dir_local, dir_online)

		print " "
		print " "
		print "REQUETTE : "
		print rsync_cmd
		print " "
		print " "

		result = 0
                #effectuer la commande rsync
		result = os.system(rsync_cmd)
		#print result
		if result != 0:
		    error = "ERROR rsync "+str(result)+" Couldn't execute"+ rsync_cmd
		    print error

		
	except mdb.Error, e:  
		error = "Error %d: %s" % (e.args[0],e.args[1])
		print error
		sys.exit(1)
		
	finally:     
		if con:    
			con.close()


def usage():
    print "Usage : uploadeur.py command"
    print "Where command can be one of :"
    print "--h, --help"
    print "--u, utilisateur de la table t_user"
    print "--s, code du serveur de la table table_portail"
    print "--m, mode 'dev||prod' qui correspond au type 0||1 de table portail"
    print "--local, facultatif pour definir un sous dossier particulier"
    print "--distant, facultatif pour definir un sous dossier particulier"

if __name__ == "__main__":
    if len(sys.argv[1:]) == 0:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hicd", ["help", "u=", "s=", "m=", "local=", "distant="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    #if os.getuid() != 0:
    #    print "Sorry you must be 'root' to run this program"
    #    sys.exit(2)
   
    user=" "
    serveur=" "
    mode=" "
    local="./"
    distant="./"
    for opt, arg in opts:
        if opt in ('--h', '--help'):
            usage()
            sys.exit()
        if opt in ('--u'):
            user= arg
        if opt in ('--s'):
            serveur = arg
        if opt in ('--m'):
            mode = arg
        if opt in ('--local'):
            local = arg
        if opt in ('--distant'):
            distant = arg

    #n executer la commande que si un minimum de param sont saisit
    if user!=" " and serveur!=" " and mode!=" ":
        upload(user,serveur,mode,local,distant)
    else:
        usage()
        sys.exit()

