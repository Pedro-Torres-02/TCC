import sys
import os

_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)


def preparar():
    import main as m
    m.etapa_preparar()
    return "preparar OK"


def sesmo():
    import main as m
    m.etapa_sesmo()
    return "sesmo OK"


def arquivar():
    import main as m
    m.etapa_arquivar()
    return "arquivar OK"
