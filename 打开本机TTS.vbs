Set objShell = CreateObject("WScript.Shell")
strPath = objShell.CurrentDirectory
objShell.Run """" & strPath & "\start_local_tts.bat""", 0, False
