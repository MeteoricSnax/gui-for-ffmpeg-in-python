import os
import subprocess


def findFiles(
    window,
    acceptedFileTypes,
    replaceVideoArgs,
    videoArgs,
    audioArgs,
    pixelFormat,
    subtitles,
    replaceAudioArgs,
    backlog,
    dirs,
    dirsToConvert,
):
    def commandBuilder(filename):
        if (
            os.path.isfile(filename)
            and os.path.splitext(os.path.join(os.getcwd(), filename))[1].lower()
            in acceptedFileTypes
        ):

            createConverted = True
            for file in os.listdir(os.getcwd()):
                if file == "converted":
                    createConverted = False
                    break
            if createConverted:
                os.mkdir("converted")

            formattetFilename = (
                filename.replace("[", "\[").replace("]", "\]").replace(",", "\,")
            )
            if filename.lower().endswith(".mp4"):
                finalName = filename.replace(
                    os.path.splitext(os.path.join(os.getcwd(), filename))[1],
                    "(converted).mp4",
                )
            else:
                finalName = filename.replace(
                    os.path.splitext(os.path.join(os.getcwd(), filename))[1], ".mp4"
                )

            transcodeCommand = 'ffmpeg -i "' + filename + '"'

            if replaceVideoArgs:
                transcodeCommand = transcodeCommand + " " + videoArgs
            else:
                transcodeCommand = (
                    transcodeCommand
                    + " -c:v hevc_nvenc "
                    + pixelFormat
                    + " "
                    + videoArgs
                )

            result = None
            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-i",
                        filename,
                        "-c",
                        "copy",
                        "-map",
                        "0:s:0",
                        "-frames:s",
                        "1",
                        "-f",
                        "null",
                        "-",
                        "-v",
                        "fatal",
                        ";",
                        "echo",
                        "$?",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError as e:
                print(e.output)
                pass

            if subtitles and len(result.stderr) == 0:
                transcodeCommand = (
                    transcodeCommand + ' -vf subtitles="' + formattetFilename + '"'
                )

            if replaceAudioArgs:
                transcodeCommand = (
                    transcodeCommand + " " + audioArgs + ' "' + finalName + '"'
                )
            else:
                transcodeCommand = (
                    transcodeCommand + " -c:a ac3 " + audioArgs + ' "' + finalName + '"'
                )

            backlog.append(
                {
                    "transcodeCommand": transcodeCommand,
                    "finalName": finalName,
                    "fileDir": os.getcwd(),
                }
            )

    for key, value in dirs.items():
        if value:
            dirsToConvert.append(key)
    for filename in dirsToConvert:
        commandBuilder(filename)
    else:
        startDir = os.getcwd()
        for directory in dirsToConvert:
            if os.path.isdir(directory):
                os.chdir(os.path.join(startDir, directory))
                for filename in os.listdir(os.getcwd()):
                    commandBuilder(filename)
        else:
            if len(backlog) >= 1:
                window.write_event_value("-filesFound-", None)
            else:
                window.write_event_value("Exit", None)
