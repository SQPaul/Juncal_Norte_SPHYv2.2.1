
def rfclas(lista_bandas,training_vector,columna):
    
    """Clasificación supervisada de imagen usando Random Forest classification con 100 trees.
    Inputs: Imagen con al menos tres bandas. Polígono de entrenamiento con columna numérica que identifica la clase.
    Ese campo debe llamarse id. Debe tener otra columna con etiqueta cualitativa describiendo 
    clase de uso de suelo. Puede tener cualquier nombre. En el ejemplo se llama "Uso".
    Outputs: imagen tif en directorio de imagen multibanda. Se muestra además gráficos de área por tipo de uso. 
    Se puede acceder además al dataframe con datos de área por uso de suelo.
    
    Ejemplo de ejecución:
    
    multiband= r'D:\LC08_001081_20190319.tif'
    poligonos=r"D:\Training_data.gpkg"
    columna="Uso"
    
    rfclas.rfclas(multiband,poligonos,columna)
    
    Si se quiere aceder a Dataframe con datos por clase
    
    newDf= randomforest(multiband,poligonos,columna)
    
    
    """
    
    import os
    import geopandas as gpd
    import rasterio 
    from rasterio import features
    from osgeo import gdal, gdal_array
    import glob
    from sklearn.ensemble import RandomForestClassifier
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import matplotlib as mpl
    import matplotlib.colors as colors
    
    
    ruta_salida= os.path.splitext(lista_bandas)[0]+"_randomforest.tif"
    bandaRast=[] #Guardamos imágenes con rasterio
    bandaNum= []#Guardamos imagenes como numpy array
    
    for i in range(rasterio.open(lista_bandas).count):
               
        read_rast= rasterio.open(lista_bandas)
        bandaRast.append(read_rast)
        read_nump= read_rast.read(i+1)
        bandaNum.append(read_nump)
        
    #Ruta al archivo shape de poligono que define las clases de uso de suelo
    shapefile = gpd.read_file(training_vector)
    shapefile.set_index("id",inplace=True)#Pondemos el identificador de la clase como índice (cambiar id por el nombre del campo numérico que contiene la clase)

    metadata= read_rast.profile
    del metadata['blockxsize']
    del metadata['blockysize']
    metadata["count"]=1
    
    #Rasterizando poligonos
    
    with rasterio.open(("Raster_train.tif"), 'w+', **metadata) as out:
        out_arr = out.read(1)

        #Creamos un generador con los datos de geometria y el identificador de los poligonos
        shapes = ((geom,value) for geom, value in zip(shapefile.geometry, shapefile.index))#Shapefile mgeometry es el campo geometry de nuestro shapefile. Shapefile.id es el campo con las clases (valor numérico)

        rasterizado = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)#Este código genera el array de numpy de los poligonos de muestra. Transform hace referencia al metadata.
        out.write_band(1, rasterizado)#Guardando el archivo rasterizado en el disco duro
       
    
      #Creando archivo multibandas

    multibanda= np.dstack((bandaNum))
    falso_color=[3,2,1]
    
    print ("Clases de uso de suelo: ",shapefile[columna].unique())
    print ("Número de pixeles de muestra: ",np.size(rasterizado[rasterizado>0]))
    
    X = multibanda[rasterizado > 0, :]#Seleccionamos los pixeles de cada banda en la posición de los pixeles con muestra
    y = rasterizado[rasterizado > 0] #Pixeles con muestra (del archivo rasterizado)
    
    # Iniciando modelo con 100 trees
    rf = RandomForestClassifier(n_estimators=100, oob_score=True)

    #Ajustando el modelo con nuestros datos (X=valor de pixel muestreado en cada banda, y=Clase de uso en archivo rasterizado)
    rf = rf.fit(X, y)
    
    print('La exactitud de nuestra predicción calculada usando out of bag score:',str(rf.oob_score_ * 100))#"(oob= out of bag sample)"
    
     #Importancia de cada banda para predecir uso de suelo
    
    print("Peso de cada banda para discriminación de clases")
    for i in range(len(rf.feature_importances_)):
        print ('Banda {a}: {b}'.format(a=str(i+1),b=(rf.feature_importances_[i]*100)))
        
    # Toma la imagen completa y la cambia de forma a un array de dos dimensiones(nfilas * ncolumnas, nbandas) para clasificación
       
    
    new_shape = (multibanda.shape[0] * multibanda.shape[1], multibanda.shape[2])
    img_as_array = multibanda[:, :, :].reshape(new_shape)

    #print("Para poder hacer la clasificación cambio de forma de",multibanda.shape[0],"filas",multibanda.shape[1],"columnas y",
          #multibanda.shape[2], "dimensiones a",img_as_array.shape[0],"filas y",img_as_array.shape[1],"columnas")
    
    # Predecir la clase de cada pixel
    class_prediction = rf.predict(img_as_array)
    # Volvemos la imagen a la forma original
    class_prediction = class_prediction.reshape(multibanda[:, :, 0].shape)
    
    metadata= read_rast.profile
    metadata["count"]=1
    metadata["dtype"]= class_prediction.dtype
    del metadata['blockxsize']
    del metadata['blockysize']
    
    with rasterio.open(ruta_salida, 'w', **metadata) as out:
        out.write(class_prediction,1)
    
    #Primero creamos dataframe sumando pixeles por clase y agregamos columna de uso de suelo de shapefile original
    
    df_clases= pd.DataFrame(class_prediction.flatten(),columns=["Clases"])#Creando dataframe con pixeles alineados en una sola columna
    df_clases["suma"]=1#Creando columna con unos para contar pixeles por clase
    area_clase= pd.pivot_table(df_clases,index="Clases",values="suma",aggfunc=np.sum)#Agrupando y contando pixeles por clase
    area_clase["Area_km2"]=(area_clase["suma"]*read_rast.transform[0]**2)/1000000 #Creando campo de area en km2
    base_final= area_clase.merge(shapefile, left_on=area_clase.index, right_on=shapefile.index, how = 'inner')
  
    #Borramos columnas auxiliares y filas duplicadas
    
    del base_final["suma"]
    del base_final["geometry"]
    del base_final["key_0"]
    base_final.drop_duplicates(subset ="Uso", inplace = True)#Elimina filas repetidas por si tengo varios poligonos de una clase
    base_final.sort_index(inplace=True)
    

    #Creando figura
    lista_colores= ['orangered','limegreen','steelblue',"linen","greenyellow","rosybrown","blue","red","dimgrey","violet","gold"]
    cmap = colors.ListedColormap(lista_colores[0:len(range(base_final.shape[0]))])#
    
    #Imagen multibanda
    
    plt.figure(figsize=(8,6),tight_layout=True)
    plt.subplot(221)
    plt.imshow(multibanda[:,:,falso_color]/np.max(multibanda))
    plt.imshow(rasterizado,alpha=0.3,cmap="binary_r")
    plt.title("Bandas "+str(falso_color)+" y muestras")

    #Imagen clasificada
    plt.subplot(222)
    plt.title('Imagen clasificada')
    plt.imshow(class_prediction,cmap=cmap)
    plt.colorbar(cmap=cmap,fraction=0.038,pad=0.03)

    #Gráfico de barras de área ocupada por cada clase

    plt.subplot(2,2,(3,4))
    plt.bar(base_final["Uso"],base_final["Area_km2"],color=lista_colores);
    plt.xlabel("Clase",fontweight="bold")
    plt.ylabel("Area Km$^2$",fontweight="bold");
    plt.xticks(rotation=20,fontsize=8,fontweight="bold");
    

    return(base_final)
