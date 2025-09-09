GenPat.exe .\kq1_clean\OBJECT .\kq1_work\OBJECT .\nsisFiles\OBJECT.patch /r
GenPat.exe .\kq1_clean\LOGDIR .\kq1_work\LOGDIR .\nsisFiles\LOGDIR.patch /r
GenPat.exe .\kq1_clean\SNDDIR .\kq1_work\SNDDIR .\nsisFiles\SNDDIR.patch /r
GenPat.exe .\kq1_clean\PICDIR .\kq1_work\PICDIR .\nsisFiles\PICDIR.patch /r 
GenPat.exe .\kq1_clean\WORDS.TOK .\kq1_work\WORDS.TOK .\nsisFiles\WORDS.TOK.patch /r
GenPat.exe .\kq1_clean\VIEWDIR .\kq1_work\VIEWDIR .\nsisFiles\VIEWDIR.patch /r
cp .\kq1_work\WORDS.TOK.EXTENDED .\nsisFiles\
makensis.exe .\nsisFiles\installer.nsi