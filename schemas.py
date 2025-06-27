from pydantic import BaseModel, Field,field_serializer
from typing import List, Optional,Dict
from datetime import datetime

# Schemas para crear detalles (usados en el endpoint POST)
class DetalleBackendCreate(BaseModel):
    Repositorio: str
    Framework: str
    Lenguaje: str
    BaseDatos: Optional[str] = None
    Alojamiento: Optional[str] = None
    SO: Optional[str] = None
    Urls: Optional[str] = None
    ServidorWeb: Optional[str] = None

class DetalleFrontendCreate(BaseModel):
    Repositorio: str
    Framework: str
    Lenguaje: str
    Alojamiento: Optional[str] = None
    SO: Optional[str] = None
    Urls: Optional[str] = None
    ServidorWeb: Optional[str] = None

class DetalleMovilCreate(BaseModel):
    Repositorio: str
    Framework: str
    Lenguaje: str
    VersionAndroid: Optional[str] = None
    VersioniOS: Optional[str] = None
    EnlaceDescarga: Optional[str] = None

# Nuevo: Schemas para tags
class ProyectoTagCreate(BaseModel):
    Tag: str

class ProyectoTag(BaseModel):
    id: int
    Tag: str
    proyecto_id: int

    class Config:
        from_attributes = True

# Schema para crear proyecto con detalles y tags
class ProyectoConDetallesCreate(BaseModel):
    id: int = Field(0, example=0)
    Sistema: str = Field(..., example="MyFinances")
    Descripcion: str = Field(..., example="Sistema para registro financiero")
    Logo: Optional[str] = None
    fecha_registro: Optional[datetime] = None

    detalle_backend: List[DetalleBackendCreate] = []
    detalle_frontend: List[DetalleFrontendCreate] = []
    detalle_movil: List[DetalleMovilCreate] = []
    detalle_tags: List[ProyectoTagCreate] = []
   

# Schemas para la respuesta (usados en response_model)
class DetalleBackend(BaseModel):
    id: int
    Repositorio: str
    Framework: str
    Lenguaje: str
    BaseDatos: Optional[str] = None
    Alojamiento: Optional[str] = None
    SO: Optional[str] = None
    Urls: Optional[str] = None
    ServidorWeb: Optional[str] = None
    proyecto_id: int

    class Config:
        from_attributes = True

class DetalleFrontend(BaseModel):
    id: int
    Repositorio: str
    Framework: str
    Lenguaje: str
    Alojamiento: Optional[str] = None
    SO: Optional[str] = None
    Urls: Optional[str] = None
    ServidorWeb: Optional[str] = None
    proyecto_id: int

    class Config:
        from_attributes = True

class DetalleMovil(BaseModel):
    id: int
    Repositorio: str
    Framework: str
    Lenguaje: str
    VersionAndroid: Optional[str] = None
    VersioniOS: Optional[str] = None
    EnlaceDescarga: Optional[str] = None
    proyecto_id: int

    class Config:
        from_attributes = True

class Proyectos(BaseModel):
    id: int
    Sistema: str
    Descripcion: str
    Logo: Optional[str] = None
    fecha_registro: Optional[datetime] = None

    detalle_backend: List[DetalleBackend] = []
    detalle_frontend: List[DetalleFrontend] = []
    detalle_movil: List[DetalleMovil] = []
    detalle_tags: List[ProyectoTag] = []  # Cambiado de Tags:str a lista de objetos

    class Config:
        from_attributes = True
        
    @field_serializer("fecha_registro")
    def serialize_fecha_registro(self, fecha: Optional[datetime]) -> Optional[str]:
        if fecha:
            return fecha.strftime("%d/%m/%Y %H:%M:%S")
        return None

class SesionActiva(BaseModel):
    id: int
    DataSesion: str

class RepositoriosFrameworks(BaseModel):
    id : int
    Framework : str
    NombreRepositorio : str
    Url : str
    Tipo : str
    fecha_registro : Optional[datetime] = None

class RepositoryInfo(BaseModel):
    name: str
    url: str
    type: str

class FrameworkSummary(BaseModel):
    count: int
    repositories: List[RepositoryInfo]

class ListarFrameworksResponse(BaseModel):
    detalles: List[RepositoriosFrameworks]
    resumen: Dict[str, FrameworkSummary]

    
