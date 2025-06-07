from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from datetime import datetime
from database import SessionLocal, engine
from models import Proyectos, DetalleBackend, DetalleFrontend, DetalleMovil, ProyectosTags
from fastapi.middleware.cors import CORSMiddleware
# Crear la aplicación FastAPI
app = FastAPI()
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



@app.post("/RegistrarProyecto/", response_model=schemas.Proyectos, status_code=status.HTTP_201_CREATED)
def RegistrarProyecto(data: schemas.ProyectoConDetallesCreate, db: Session = Depends(get_db)):
    # 1. Crear o actualizar el proyecto principal
    
    if not data.id or data.id == 0:
        db_proyecto = Proyectos(
            Sistema=data.Sistema,
            Descripcion=data.Descripcion,
            Logo=data.Logo,
            fecha_registro=datetime.now()
        )
        db.add(db_proyecto)
        db.commit()
        db.refresh(db_proyecto)
        status_code_ = status.HTTP_201_CREATED
    else:
        db_proyecto = db.query(Proyectos).get(data.id)
        if not db_proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto con ID {data.id} no encontrado"
            )
        db_proyecto.Sistema = data.Sistema
        db_proyecto.Descripcion = data.Descripcion
        db_proyecto.Logo = data.Logo
        db.commit()
        status_code_ = status.HTTP_200_OK

    # 2. Limpiar detalles anteriores si es una actualización
    if data.id and data.id != 0:
        db.query(DetalleBackend).filter(DetalleBackend.proyecto_id == db_proyecto.id).delete()
        db.query(DetalleFrontend).filter(DetalleFrontend.proyecto_id == db_proyecto.id).delete()
        db.query(DetalleMovil).filter(DetalleMovil.proyecto_id == db_proyecto.id).delete()
        db.query(ProyectosTags).filter(ProyectosTags.proyecto_id == db_proyecto.id).delete()
        db.commit()

    # 3. Insertar nuevos detalles Backend
    if data.detalle_backend:
        nuevos_detalles_backend = [
            DetalleBackend(
                Repositorio=detalle.Repositorio,
                Framework=detalle.Framework,
                Lenguaje=detalle.Lenguaje,
                BaseDatos=detalle.BaseDatos,
                Alojamiento=detalle.Alojamiento,
                SO=detalle.SO,
                Urls=detalle.Urls,
                ServidorWeb=detalle.ServidorWeb,
                proyecto_id=db_proyecto.id
            )
            for detalle in data.detalle_backend
        ]
        db.bulk_save_objects(nuevos_detalles_backend)
        db.commit()

    # 4. Insertar nuevos detalles Frontend
    if data.detalle_frontend:
        nuevos_detalles_frontend = [
            DetalleFrontend(
                Repositorio=detalle.Repositorio,
                Framework=detalle.Framework,
                Lenguaje=detalle.Lenguaje,
                Alojamiento=detalle.Alojamiento,
                SO=detalle.SO,
                Urls=detalle.Urls,
                ServidorWeb=detalle.ServidorWeb,
                proyecto_id=db_proyecto.id
            )
            for detalle in data.detalle_frontend
        ]
        db.bulk_save_objects(nuevos_detalles_frontend)
        db.commit()

    # 5. Insertar nuevos detalles Móvil
    if data.detalle_movil:
        nuevos_detalles_movil = [
            DetalleMovil(
                Repositorio=detalle.Repositorio,
                Framework=detalle.Framework,
                Lenguaje=detalle.Lenguaje,
                VersionAndroid=detalle.VersionAndroid,
                VersioniOS=detalle.VersioniOS,
                EnlaceDescarga=detalle.EnlaceDescarga,
                proyecto_id=db_proyecto.id
            )
            for detalle in data.detalle_movil
        ]
        db.bulk_save_objects(nuevos_detalles_movil)
        db.commit()

    # 6. Insertar nuevos Tags
    if data.detalle_tags:
        nuevos_tags = [
            ProyectosTags(
                Tag=tag.Tag,
                proyecto_id=db_proyecto.id
            )
            for tag in data.detalle_tags
        ]
        db.bulk_save_objects(nuevos_tags)
        db.commit()

    return db_proyecto



@app.delete("/EliminarProyecto/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
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
def listar_proyectos(id: int, db: Session = Depends(get_db)):
    if id == 0:
        # Listar todos los proyectos con sus detalles
        proyectos = db.query(models.Proyectos).all()
    else:
        # Buscar el proyecto específico con sus detalles
        proyecto = db.query(models.Proyectos).filter(models.Proyectos.id == id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        proyectos = [proyecto]  # Para unificar la respuesta como lista

    return proyectos

# Endpoint de prueba
@app.get("/")
def read_root():
    return {"message": "API de Proyectos funcionando correctamente"}
    

