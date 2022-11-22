def landsat8(poligono,nubes,startD,endD):
    
    """Descarga de imágenes Landsat 8 a google Drive en carpeta Landsat_images. Inputs 
    ruta polígono de interés, porcentaje máximo de nubes, fecha inicio del periodo de búsqueda,fecha final periodo de búsqueda.
    Ejemplo: landsat8("poligono.gpkg",20,"2013-04-20","2013-05-20")
    El archivo se guarda en Google Drive en carpeta Landsat_images"""
    
    "version 15-04-2022"
    
    import ee
    ee.Initialize()
    import datetime
    import pandas as pd
    import geopandas as gpd
    import os
    import glob
    from shapely.geometry import MultiPoint,Point
    import warnings
    from IPython.display import display,Markdown
    import sys
    warnings.filterwarnings('ignore')
    

    #Colección de imágenes a analizar
    coleccion= "LANDSAT/LC08/C01/T1_SR" #"LANDSAT/LT05/C01/T1_SR"    
     #Enable fiona driver
    gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
    
    startDate= str(startD)
    endDate= str(endD)
    ruta = os.path.dirname(poligono) ## dir of dir of file
    carpeta = os.path.split(ruta)[1]

    pointList=[]
    shapeFile = gpd.read_file(poligono)
    shapeFile["Dis"]=1
    shapeFile= shapeFile.dissolve(by='Dis')
    crs_poligono= str(shapeFile.crs)

    #Buscando vertices y transformandolo a puntos
    a= shapeFile.bounds
    x= [float(a.minx),float(a.minx),float(a.maxx),float(a.maxx)]
    y = [float(a.maxy),float(a.miny),float(a.miny),float(a.maxy)]
    df= pd.DataFrame({"x":x,"y":y})
    geo= gpd.GeoDataFrame(df,geometry=[Point(xy) for xy in zip(df.x, df.y)],crs=crs_poligono)

    #Guardandolo en coordenadas geograficas
    area= geo.to_crs({'init': 'epsg:4326'})
    area["x"] = area.centroid.map(lambda p: p.x)
    area["y"] = area.centroid.map(lambda p: p.y)
    new = area[["x","y"]].values.tolist()

    roi = ee.Geometry.Polygon(new);

    #Filtrando colección por nubosidad, localización y fechas
    le8 = ee.ImageCollection(coleccion).filterDate(startDate, endDate).filterBounds(roi).filter(ee.Filter.lessThanOrEquals('CLOUD_COVER', nubes))

    id_imagen= []
    nubosidad=[]
    fecha=[]

    for images in le8.getInfo()['features']:
        name= images["properties"]['system:index']
        cloud=images["properties"]["CLOUD_COVER"]
        time= images["properties"]["SENSING_TIME"]
        nubosidad.append(cloud)
        id_imagen.append(name)
        fecha.append(time)

        #Creando dataframe con metadata de imagenes

        landsat= pd.DataFrame({"nubosidad":nubosidad,"id":id_imagen})
        landsat["fecha"]=pd.to_datetime(fecha)
        landsat["year"]=pd.DatetimeIndex(landsat['fecha']).year
        landsat["day"]=pd.DatetimeIndex(landsat['fecha']).day
        landsat["month"]=pd.DatetimeIndex(landsat['fecha']).month
        landsat.set_index('fecha', inplace=True)
        #landsat.sort_index(inplace=True)
    
    if "landsat" not in locals():
        print("No hay imágenes disponibles")
        return
        
    else:
   
        print('\033[1m' +"Lista de imágenes disponibles: "+'\033[0m')
        display(landsat)

        download= input("¿Desea descargar las imágenes?: (escriba si o no)")

    if download == "si":           

        #Folder puede ser cualquier carpeta que tenga respaldada en DRIVE. Sólo va el nombre no la ruta

        roi = ee.Geometry.Polygon(new)

        landsat = ee.ImageCollection(coleccion).filterDate(startDate, endDate).filterBounds(roi).filter(ee.Filter.lessThanOrEquals('CLOUD_COVER_LAND', nubes))

        for images in landsat.getInfo()['features']:
            image1 = ee.Image(images["id"]).select(['B1',"B2","B3","B4","B5","B6","B7"])
            name= images["properties"]['system:index']

            task=ee.batch.Export.image.toDrive(image= image1,
                                           description=name,
                                           scale= 30,
                                           folder="Landsat_images",
                                           crs= crs_poligono,
                                           region= roi)
            task.start()

        print("Descarga comenzada!! Pueden demorar unos minutos en aparacer las imágenes en Google Drive")
        
    else:
        print("Descarga abortada")
 
