using System.Diagnostics;

RunScript("translation.py");

static void RunScript(string scriptName)
{
    var pathToProject = "C:\\Users\\Dawid\\Projectos\\los_enginneros";
    var activateVenv = ".venv\\Scripts\\activate.bat";
    var installCommand = "pip3 install translators";
    var pythonCommand = $"python3 {scriptName}";
    
    var start = new ProcessStartInfo
    {
        FileName = "cmd.exe",
        Arguments = $"/k cd {pathToProject} && {activateVenv}",
        //UseShellExecute = false,
        RedirectStandardInput = true,
        //CreateNoWindow = true
    };
    
    var process = Process.Start(start);
    
    StreamWriter writer = process.StandardInput;
    writer.WriteLine(installCommand);
    writer.WriteLine(pythonCommand);
}
