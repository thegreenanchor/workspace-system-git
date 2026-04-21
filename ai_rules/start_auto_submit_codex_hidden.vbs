Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = Chr(34) & "C:\Python314\python.exe" & Chr(34)
scriptPath = Chr(34) & scriptDir & "\auto_submit_codex_sessions.py" & Chr(34)

shell.Run pythonExe & " " & scriptPath & " --all", 0, False
