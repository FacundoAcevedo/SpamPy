SpamPy
======

Pequeño script para identificar spam en la cola de mailq

Uso: spampy.py [-h] [-v] [-c CORREO | -f | -s]

Argumentos opcionales:
  -h, --help            show this help message and exit
  -v, --verbose         Muestra un poco mas de info
  -c CORREO, --correo CORREO
                        Correo usado como filtro
  -f, --borrarTodo      Borra toda la cola del mailq
  -s, --spam            Lista los id de correo spam
