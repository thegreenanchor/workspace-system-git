Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
workerCmd = Chr(34) & scriptDir & "\auto_cli_broker_worker.cmd" & Chr(34)

shell.Run shell.ExpandEnvironmentStrings("%ComSpec%") & " /c " & workerCmd, 0, False
