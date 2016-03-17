
import threading
import time
import subprocess

import wayround_org.getthesource.mirrorer


class Wget:

    def __init__(
            self,
            downloader,
            uri,
            outputdir,
            new_basename=None,
            stop_event=None,
            ignore_invalid_connection_security=False,
            downloader_obfuscation_required=False
            ):

        self._downloader = downloader

        self._process = None
        self._stop_event = stop_event
        self._own_stop_event = threading.Event()

        self._logger = self._downloader.logger

        self._start_lock = threading.Lock()

        self._internal_started_waiter_flag = threading.Event()

        self._process_result = None

        self.uri = uri
        self.outputdir = outputdir
        self.new_basename = new_basename

        self.ignore_invalid_connection_security =\
            ignore_invalid_connection_security

        self.downloader_obfuscation_required =\
            downloader_obfuscation_required

        return

    def _stop_flag_watcher(self):
        while True:
            if self._own_stop_event.is_set():
                break
            if self._stop_event is not None and self._stop_event.is_set():
                break
            time.sleep(1)

        threading.Thread(target=self.stop).start()

        return

    def _program_exit_waiter(self):

        output_filename_options = [
            '-O',
            wayround_org.utils.path.join(
                self.outputdir,
                self.new_basename
                )
            ]

        connection_sec_check_options = []
        if self.ignore_invalid_connection_security:
            connection_sec_check_options.append('--no-check-certificate')

        cmd_line = (
            ['wget'] + ['-c'] +
            output_filename_options +
            connection_sec_check_options +
            [self.uri]
            )

        self._logger.info("wget command is: {}".format(cmd_line))

        try:
            self._process = subprocess.Popen(
                cmd_line,
                stdin=subprocess.DEVNULL,
                stdout=self._logger.stdout,
                stderr=self._logger.stderr,
                # bufsize=0
                )
        except:
            self._logger.exception(
                "program starting error: {}".format(cmd_line)
                )

        self._internal_started_waiter_flag.set()
        ret = self._process.wait()
        self._logger.info("process exited with code: {}".format(ret))
        self._process_result = ret
        threading.Thread(target=self.stop).start()
        return

    def start(self):
        with self._start_lock:
            if self._process is None:
                threading.Thread(target=self._program_exit_waiter).start()
                self._internal_started_waiter_flag.wait()

        return

    def _stop(self):
        self._own_stop_event.set()
        try:
            self._process.terminate()
            time.sleep(3)
        except:
            self._logger.exception("error")

        # TODO: it is better to know somehow other way, but not using bloody
        #       kill though
        try:
            self._process.kill()
        except:
            self._logger.exception("error")

        return

    def stop(self):
        # NOTE: _stop() contains waitings based on time, so they must not block
        #       programm
        threading.Thread(target=self._stop).start()
        return

    def wait(self):

        if self._process is None:
            raise Exception("can't wait for end of what is not started yet")

        while True:

            if self._own_stop_event.is_set():
                break

        return self._process_result


class Downloader:

    def __init__(self, controller):
        if not isinstance(
                controller,
                wayround_org.getthesource.mirrorer.Mirrorer
                ):
            raise TypeError(
                "`controller' must be inst of "
                "wayround_org.getthesource.mirrorer.Mirrorer"
                )
        self.controller = controller
        self.logger = self.controller.logger

        return

    def get_downloader_name(self):
        return 'GNU/Wget'

    def get_downloader_code_name(self):
        return 'wget'

    def get_supported_schemas(self):
        return ['http', 'https', 'ftp']

    def get_is_downloader_enabled(self):
        return True

    def download(
            self,
            uri,
            outputdir,
            new_basename=None,
            stop_event=None,
            ignore_invalid_connection_security=False,
            downloader_obfuscation_required=False
            ):
        """
        return: True - ok, None - error, False - ok, but download not completed
        """

        ret = True

        proc = Wget(
            self,
            uri,
            outputdir,
            new_basename=new_basename,
            stop_event=stop_event,
            ignore_invalid_connection_security=(
                ignore_invalid_connection_security
                ),
            downloader_obfuscation_required=(
                downloader_obfuscation_required
                )
            )
        proc.start()
        ret = proc.wait()

        return ret
