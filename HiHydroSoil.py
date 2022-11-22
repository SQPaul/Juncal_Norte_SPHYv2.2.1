#!/usr/bin/env python
# coding: utf-8

# # HiHydroSoil to SPHY
# ## Juncal Norte - august, 2022
# #### Paul Sandoval Quilodrán - https://github.com/SQPaul
# #### Run in QGIS

# ### Import packages

# In[ ]:


import glob


# ## Selecting useful data

# In[ ]:


hydrosoil = glob.glob("/media/phi/SANDOVAL/Juncal_norte/SOIL_PROPERTIES/*.tif") #r"/media/phi/SANDOVAL/LAST PAUL/VI año/Memoria de título/Modelación/Soil_properties#/*.tif" 

for i in hydrosoil:
    name = i[49:-8]
    #print(name)
    if name == "WCpF2_M_250m_TOPSOIL":
        R_FC = i
    elif name == "WCsat_M_250m_TOPSOIL":
        R_SC = i
    elif name == "WCpF42_M_250m_TOPSOIL":
        R_PWP = i
    elif name == "WCpF3_M_250m_TOPSOIL":
        R_WP = i
    elif name == "Ksat_M_250m_TOPSOIL":
        R_KSAT = i
    elif name == "WCpF2_M_250m_SUBSOIL":
        S_FC = i
    elif name == "WCsat_M_250m_SUBSOIL":
        S_SC = i
    elif name == "Ksat_M_250m_SUBSOIL":
        S_KSAT = i
        
hydrosoil_sel = [R_FC,R_SC,R_PWP,R_WP,R_KSAT,S_FC,S_SC,S_KSAT] 


# ## Resampling HiHydroSoil 
# ### Change crs, resolution and extent

# In[ ]:


for i in hydrosoil_sel:
    output = i[:-4]+"_mod.tif"
    processing.run("gdal:warpreproject", 
               {'INPUT':str(i),
                'SOURCE_CRS':None,
                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:32719'),
                'RESAMPLING':0,'NODATA':None,
                'TARGET_RESOLUTION':500,
                'OPTIONS':'',
                'DATA_TYPE':0,
                'TARGET_EXTENT':'380681.000000000,413181.000000000,6339419.000000000,6381419.000000000 [EPSG:32719]',
                'TARGET_EXTENT_CRS':None,
                'MULTITHREADING':False,
                'EXTRA':'',
                'OUTPUT':str(output)})


# ## Rasterio & Gdal way

# ## Rasterio & Gdal way 2

# ## Gdal way

# ## Multiply each raster (*0.0001)

# ## Cut raster by masklayer

# In[ ]:




