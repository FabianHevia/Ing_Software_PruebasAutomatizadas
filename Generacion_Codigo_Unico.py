import random
import string

def Generacion_Codigo_Unico(length=20):
    caracteres = string.ascii_letters + string.digits
    codigo_unico = ''.join(random.choice(caracteres) for _ in range(length))
    return codigo_unico

# Generate a 20-character unique code
codigo = Generacion_Codigo_Unico()
print("El codigo unico es:", codigo)
