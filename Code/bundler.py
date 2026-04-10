import config
import shutil
import urllib.request
import os

def pack_epd():
    shutil.make_archive(f"{config.CACHE_DIR}/EPD_DATA", "xztar", f"{config.CACHE_DIR}/EPD_Dataset/")

def unpack_epd():
    if os.path.isdir(f"{config.CACHE_DIR}/EPD_Dataset/"):
        print("Folder already exists! Not unpacking")
        return
    shutil.unpack_archive(f"{config.CACHE_DIR}/EPD_DATA.tar.xz", f"{config.CACHE_DIR}/EPD_Dataset/")

def download_epd():
    if not os.path.isfile(f"{config.CACHE_DIR}/EPD_DATA.tar.xz"):
        urllib.request.urlretrieve("https://projects.pmodwrc.ch/flaretool/EPD_DATA.tar.xz", 
                                f"{config.CACHE_DIR}/EPD_DATA.tar.xz")

def pack_connectivity_tool():
    shutil.make_archive(f"{config.CACHE_DIR}/CON_DATA", "xztar", f"{config.CACHE_DIR}/connectivity_tool_downloads/")

def unpack_connectivity_tool():
    if os.path.isdir(f"{config.CACHE_DIR}/connectivity_tool_downloads/"):
        print("Folder already exists! Not unpacking")
        return
    shutil.unpack_archive(f"{config.CACHE_DIR}/CON_DATA.tar.xz", f"{config.CACHE_DIR}/connectivity_tool_downloads/")


def download_connectivity_tool():
    if not os.path.isfile(f"{config.CACHE_DIR}/CON_DATA.tar.xz"):
        urllib.request.urlretrieve("https://projects.pmodwrc.ch/flaretool/CON_DATA.tar.xz", 
                                f"{config.CACHE_DIR}/CON_DATA.tar.xz")

def pack_monthly():
    shutil.make_archive(f"{config.CACHE_DIR}/monthly", "xztar", f"{config.CACHE_DIR}/monthly/")

def unpack_monthly():
    if os.path.isdir(f"{config.CACHE_DIR}/monthly/"):
        print("Folder already exists! Not unpacking")
        return
    shutil.unpack_archive(f"{config.CACHE_DIR}/monthly.tar.xz", f"{config.CACHE_DIR}/monthly/")

def download_monthly():
    if not os.path.isfile(f"{config.CACHE_DIR}/monthly.tar.xz"):
        urllib.request.urlretrieve("https://projects.pmodwrc.ch/flaretool/monthly.tar.xz", 
                                f"{config.CACHE_DIR}/monthly.tar.xz")


def auto_download():
    print("Starting Download...")
    download_epd()
    print("Finished EPD-Download")
    download_connectivity_tool()
    print("Finished CON-Download")
    download_monthly()
    print("Finished Monthly-Download")
    unpack_epd()
    unpack_connectivity_tool()
    unpack_monthly()
    print("Finished Setup")





if __name__ == "__main__":
    pack_epd()
    pack_connectivity_tool()
    pack_monthly()