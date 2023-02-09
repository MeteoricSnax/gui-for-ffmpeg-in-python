import traceback
import PySimpleGUI as sg
import os
import subprocess
import shutil

# to compile into .exe run: python -m PyInstaller .\main.py --onefile

from progresswindow import progressWindow

startDir = os.getcwd()
dirsAtStart = os.listdir(startDir)
rootConvertPath = os.path.join(startDir, "converted")

videoArgs = ""
replaceVideoArgs = False
audioArgs = ""
replaceAudioArgs = False
dirs = {}
acceptedFileTypes = (".mkv", ".mp4", ".webm")
pixelFormat = "-pix_fmt p010le"
pixelFormats = {"10-bit": "-pix_fmt p010le", "8-bit": "-pix_fmt yuv420p"}
dirsToConvert = []
subtitles = True
backlog = []
pidList = []
transferToServer = True
destinationPath = "\\\\TUF-AX5400-1B00\Torrents"


def transcode(window, transcodeCommand, finalName, fileDir):
    def transcodeFunc():
        os.chdir(fileDir)
        proc = subprocess.Popen(
            args=transcodeCommand,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        pidList.append(proc.pid)
        proc.wait()
        convertedFile = os.path.join(os.getcwd(), finalName)
        convertedDist = os.path.join(os.getcwd(), "converted", finalName)
        if os.path.exists(convertedDist):
            os.remove(convertedDist)
        os.rename(str(convertedFile), str(convertedDist))

    window.perform_long_operation(transcodeFunc, "-TRANSCODE- transcodeDone")


def moveDirsToConverted():
    os.chdir(startDir)
    rootConvertPath = os.path.join(startDir, "converted")
    for directory in dirsToConvert:
        if os.path.isdir(directory):
            os.chdir(os.path.join(startDir, directory))
            if not os.path.isdir(rootConvertPath):
                os.mkdir(rootConvertPath)
            dirConvert = os.path.join(startDir, directory, "converted")
            renamedConvert = os.path.join(rootConvertPath, directory)
            if os.path.exists(renamedConvert):
                shutil.rmtree(renamedConvert)
            os.rename(dirConvert, renamedConvert)
        os.chdir(startDir)


def transferFilesToServer(window):
    os.chdir(os.path.join(startDir, "converted"))
    filesToMove = os.listdir(os.getcwd())

    for dir in filesToMove:
        litteralPath = os.path.join(os.getcwd(), dir)
        # trimmedDistPath = destinationPath + "/"
        # moveCommand = 'powershell.exe Move-Item -LiteralPath "\'{0}\'" -Destination "{1}" -Force'.format(
        #     litteralPath, trimmedDistPath
        # )
        window.write_event_value(("movingFiles:" + dir), None)
        # proc = subprocess.Popen(args=moveCommand, shell=True)
        # poll = proc.poll()
        # while poll is None:
        #     time.sleep(0.5)
        #     window.write_event_value(("movingFiles:" + dir), None)
        #     poll = proc.poll()
        shutil.move(litteralPath, destinationPath)


layout = [
    [
        sg.Text(text="Include default subtitle track: "),
        sg.Checkbox(text="", default=True, key="subtitles", enable_events=True),
    ],
    [
        sg.Checkbox(text="Replace video args", default=False, key="replaceVideoArgs"),
        sg.Input(
            default_text="",
            s=100,
            expand_x=True,
            key="videoArgs",
            tooltip="Video arguments added to the ffmpeg transcoder",
            enable_events=True,
        ),
    ],
    [
        sg.Checkbox(text="Replace audio args", default=False, key="replaceAudioArgs"),
        sg.Input(
            default_text="",
            s=100,
            expand_x=True,
            key="audioArgs",
            tooltip='Standard audio args is: " -c:a ac3 "',
            enable_events=True,
        ),
    ],
    [
        sg.Text(text="Pixel format: "),
        sg.Radio(
            key="pixelformat 10-bit",
            text="10-bit",
            group_id="pixel format",
            default=True,
            enable_events=True,
            tooltip="-pix_fmt p010le",
        ),
        sg.Radio(
            key="pixelformat 8-bit",
            text="8-bit",
            group_id="pixel format",
            default=False,
            enable_events=True,
            tooltip="-pix_fmt yuv420p",
        ),
    ],
    [
        sg.Text(text="Move all converted files to destination folder:"),
        sg.Checkbox(text="", default=True, key="transferToServer", enable_events=True),
    ],
    [
        sg.Text(
            text="Destination folder:",
            tooltip="standard file dist is: \\\\TUF-AX5400-1B00\Torrents",
        ),
        sg.Input(key="fileDist", change_submits=True),
        sg.FolderBrowse(key="fileDist", change_submits=True),
    ],
]

for dir in dirsAtStart:
    if (
        os.path.isdir(dir)
        and any(fname.lower().endswith(acceptedFileTypes) for fname in os.listdir(dir))
        and (not (dir == "converted" or dir.startswith("_", 0, 1)))
    ):
        layout.append(
            [
                sg.Checkbox(
                    text=dir, default=True, enable_events=True, key=("dir:" + str(dir))
                )
            ]
        )
        dirs[dir] = True
    if dir.lower().endswith(acceptedFileTypes):
        layout.append(
            [
                sg.Checkbox(
                    text=dir, default=True, enable_events=True, key=("dir:" + str(dir))
                )
            ]
        )
        dirs[dir] = True

layout.append([sg.Button("Start"), sg.Button("Cancel")])

window = sg.Window(title="Video converter", layout=layout, margins=(20, 20))

try:
    while True:
        event, values = window.read()
        if event in (None, "Exit", "Cancel") or event == sg.WIN_CLOSED:
            for pid in pidList:
                subprocess.Popen(
                    "TASKKILL /PID " + str(pid) + " /F /T",
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            window.close()
            break
        elif event == "Start":
            window.close()
            progressWindow(
                pidList,
                # findFiles,
                backlog,
                transcode,
                transferToServer,
                moveDirsToConverted,
                transferFilesToServer,
                acceptedFileTypes,
                replaceVideoArgs,
                videoArgs,
                audioArgs,
                pixelFormat,
                subtitles,
                replaceAudioArgs,
                dirs,
                dirsToConvert,
            )
        elif event == "transferToServer":
            transferToServer = values["transferToServer"]
        elif event == "subtitles":
            subtitles = values["subtitles"]
        elif "dir:" in event:
            key = str(event).split(":")[1]
            if os.path.isdir(key) or os.path.isfile(key):
                dirs[key] = values[event]
        elif event == "audioArgs":
            audioArgs = values["audioArgs"]
        elif event == "videoArgs":
            videoArgs = values["videoArgs"]
        elif event == "replaceVideoArgs":
            replaceVideoArgs = values["replaceVideoArgs"]
        elif event == "replaceAudioArgs":
            replaceAudioArgs = values["replaceAudioArgs"]
        elif "pixelformat" in event:
            pixelFormat = pixelFormats[str(event).split(" ")[1]]
        elif event == "fileDist":
            destinationPath = values["fileDist"]
except Exception as e:
    tb = traceback.format_exc()
    sg.Print(f"An error has occured. here is info: ", e, tb)
    sg.popup_error(f"AN EXCEPTION OCCURRED!", e, tb)
