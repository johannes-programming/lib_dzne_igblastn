import contextlib as _contextlib
import os as _os
import shutil as _shutil
import tempfile as _tempfile

import handle_igblastn as _hi
import lib_dzne_filedata as _fd

import lib_dzne_igblastn._parsers as _prs


def get_cline(
    prog,
    *, 
    query, 
    out, 
    auxiliary_data,
    germline_db_V,
    germline_db_D,
    germline_db_J,
):
    return list(
        _hi.Cline(
            cmd=prog,
            auxiliary_data=auxiliary_data,
            germline_db_V=germline_db_V,
            germline_db_D=germline_db_D,
            germline_db_J=germline_db_J,
            query=query, 
            out=out,
        )
    )


def igdata(IGDATA, *, directory):
    src = _os.path.join(IGDATA, 'internal_data')
    dest = _os.path.join(directory, 'internal_data')
    _shutil.copytree(src, dest)
    _os.environ['IGDATA'] = directory

def parse(text):
    return _fd.TOMLData(_prs.Parser.parse_text(text))



    
