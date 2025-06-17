from fastapi import FastAPI, Depends, HTTPException, status,Header
from sqlalchemy.orm import Session
from typing import List,Optional,Union
import models
import schemas
from datetime import datetime
from database import SessionLocal, engine
from models import Proyectos, DetalleBackend, DetalleFrontend, DetalleMovil, ProyectosTags
from fastapi.middleware.cors import CORSMiddleware
import os, uuid, json
from datetime import datetime
import shutil
from fastapi import UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from dotenv import load_dotenv
# Crear la aplicación FastAPI
load_dotenv()
API_KEY = os.getenv('API_KEY')
PSW= os.getenv('PSW')

app = FastAPI()
UPLOAD_DIR = "uploads/logos"  # Carpeta donde se guardarán los archivos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Crea la carpeta si no existe
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency para obtener sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
app.dependency_overrides[verify_api_key] = verify_api_key

@app.post("/RegistrarProyecto/", response_model=schemas.Proyectos, status_code=status.HTTP_201_CREATED)
async def RegistrarProyecto(
    Sistema: str = Form(...),
    Descripcion: str = Form(...),
    id: int = Form(0),
    detalle_backend: str = Form(None),
    detalle_frontend: str = Form(None),
    detalle_movil: str = Form(None),
    detalle_tags: str = Form(None),
    Logo: Union[UploadFile, str, None] = File(None),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    import os, uuid, json
    from datetime import datetime
    import shutil
    
    print("===== DATOS RECIBIDOS =====")
    print(f"Sistema: {Sistema}")
    print(f"Descripcion: {Descripcion}")
    print(f"id: {id}")
    print(f"detalle_backend: {detalle_backend}")
    print(f"detalle_frontend: {detalle_frontend}")
    print(f"detalle_movil: {detalle_movil}")
    print(f"detalle_tags: {detalle_tags}")
    print(f"Logo: {type(Logo)} -> {getattr(Logo, 'filename', Logo)}")
    print("============================")


    # Guardar archivo si viene
    logo_path = None
    
    # if len(Descripcion)>1:
    #     raise HTTPException(status_code=404, detail="ERROR DE PRUEBA")
    # if Logo:
    if isinstance(Logo, (UploadFile, StarletteUploadFile)):
        ext = os.path.splitext(Logo.filename)[1]
        logo_name = f"{uuid.uuid4().hex}{ext}"
        save_path = f"uploads/logos/{logo_name}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(Logo.file, f)
        logo_path = save_path

    if not id or id == 0:
        db_proyecto = Proyectos(
            Sistema=Sistema,
            Descripcion=Descripcion,
            Logo=logo_path,
            fecha_registro=datetime.now()
        )
        db.add(db_proyecto)
        db.commit()
        db.refresh(db_proyecto)
        status_code_ = status.HTTP_201_CREATED
    else:
        db_proyecto = db.query(Proyectos).get(id)
        if not db_proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        db_proyecto.Sistema = Sistema
        db_proyecto.Descripcion = Descripcion
        if logo_path:
            db_proyecto.Logo = logo_path
        db.commit()
        status_code_ = status.HTTP_200_OK

    # Cargar listas anidadas desde los JSON en string
    def parse_json_list(json_str):
        return json.loads(json_str) if json_str else []

    detalle_backend = parse_json_list(detalle_backend)
    detalle_frontend = parse_json_list(detalle_frontend)
    detalle_movil = parse_json_list(detalle_movil)
    detalle_tags = parse_json_list(detalle_tags)

    # Eliminar datos anteriores si es edición
    if id and id != 0:
        print('entro')
        db.query(DetalleBackend).filter_by(proyecto_id=db_proyecto.id).delete()
        db.query(DetalleFrontend).filter_by(proyecto_id=db_proyecto.id).delete()
        db.query(DetalleMovil).filter_by(proyecto_id=db_proyecto.id).delete()
        db.query(ProyectosTags).filter_by(proyecto_id=db_proyecto.id).delete()
        db.commit()
    else:
        print('NO entro')
    # Insertar nuevos detalles
    # if detalle_backend:
    #     db.bulk_save_objects([
    #         DetalleBackend(**detalle, proyecto_id=db_proyecto.id) for detalle in detalle_backend
    #     ])
    if detalle_backend:
        db.bulk_save_objects([
            DetalleBackend(**{**{k: v for k, v in detalle.items() if k != "proyecto_id"}, "proyecto_id": db_proyecto.id})
            for detalle in detalle_backend
        ])

    # if detalle_frontend:
    #     db.bulk_save_objects([
    #         DetalleFrontend(**detalle, proyecto_id=db_proyecto.id) for detalle in detalle_frontend
    #     ])
    if detalle_frontend:
        db.bulk_save_objects([
            DetalleFrontend(**{**{k: v for k, v in detalle.items() if k != "proyecto_id"}, "proyecto_id": db_proyecto.id})
            for detalle in detalle_frontend
        ])

    # if detalle_movil:
    #     db.bulk_save_objects([
    #         DetalleMovil(**detalle, proyecto_id=db_proyecto.id) for detalle in detalle_movil
    #     ])
    if detalle_movil:
        db.bulk_save_objects([
            DetalleMovil(**{**{k: v for k, v in detalle.items() if k != "proyecto_id"}, "proyecto_id": db_proyecto.id})
            for detalle in detalle_movil
        ])
    if detalle_tags:
        db.bulk_save_objects([
            ProyectosTags(Tag=tag["Tag"], proyecto_id=db_proyecto.id) for tag in detalle_tags
        ])
    db.commit()

    return db_proyecto


@app.delete("/EliminarProyecto/{proyecto_id}", status_code=status.HTTP_200_OK)
def EliminarProyecto(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyectos).get(proyecto_id)
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proyecto con ID {proyecto_id} no encontrado"
        )
    
    
  
    db.query(models.ProyectosTags).filter(
        models.ProyectosTags.proyecto_id == proyecto_id
    ).delete()
    

    db.query(models.DetalleBackend).filter(
        models.DetalleBackend.proyecto_id == proyecto_id
    ).delete()
    

    db.query(models.DetalleFrontend).filter(
        models.DetalleFrontend.proyecto_id == proyecto_id
    ).delete()
    

    db.query(models.DetalleMovil).filter(
        models.DetalleMovil.proyecto_id == proyecto_id
    ).delete()
    

    db.delete(proyecto)
    

    db.commit()
    return



@app.get("/ListarProyectos/{id}", response_model=List[schemas.Proyectos])
def listar_proyectos(request: Request,id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    base_url = str(request.base_url)
    if id == 0:
        # Listar todos los proyectos con sus detalles
        proyectos = db.query(models.Proyectos).all()
    else:
        # Buscar el proyecto específico con sus detalles
        proyecto = db.query(models.Proyectos).filter(models.Proyectos.id == id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        proyectos = [proyecto]  # Para unificar la respuesta como lista
    for proyecto in proyectos:
        if proyecto.Logo:
            proyecto.Logo = f"{base_url}{proyecto.Logo}"
    return proyectos

@app.post("/ValidarPass/")
async def validar_contrasena(password: str = Form(...)):
    if password != PSW:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    return {"mensaje": "Contraseña válida"}

# Endpoint de prueba
@app.get("/")
def read_root():
    return {"message": "API de Proyectos funcionando correctamente"}
    

