"""
OS Specific User Files is released under the MIT license.

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""
import sublime
import sublime_plugin
import os
import shutil
import threading
import json

osplatform = sublime.platform()
user = os.path.join(sublime.packages_path(), 'User')
plugin_storage = os.path.join(user, 'OsSpecificUserFiles')
ospath = os.path.join(plugin_storage, osplatform)
settings = 'os_specific_user_files.sublime-settings'
running_thread = True


def os_specific_alert():
    sublime.error_message('OS Specific User Files encountered one or more errors.\nPlease see the console for more info.')


def run_copy_thread(force=False):
    if not running_thread:
        t = CopyOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()


def setup():
    file_errors = []
    file_storage = plugin_storage
    linux_dir = os.path.join(file_storage, 'linux')
    windows_dir = os.path.join(file_storage, 'windows')
    mac_dir = os.path.join(file_storage, 'osx')
    settings_file = os.path.join(user, settings)

    # Create main plugin storage directory
    if not os.path.exists(file_storage):
        if make_dir(file_storage):
            file_errors.append(file_storage)

    # Create OS specific folders under main storage directory
    if len(file_errors) == 0:
        if not os.path.exists(linux_dir):
            if make_dir(linux_dir):
                file_errors.append(linux_dir)
        if not os.path.exists(windows_dir):
            if make_dir(windows_dir):
                file_errors.append(windows_dir)
        if not os.path.exists(mac_dir):
            if make_dir(mac_dir):
                file_errors.append(mac_dir)

    # Create settings file
    if not os.path.exists(settings_file):
        try:
            with open(settings_file, 'w') as f:
                settings_template = {
                    "windows": {
                        "files": {
                        },
                        "directories": {
                        },
                        "rename": {
                        }
                    },
                    "osx": {
                        "files": {
                        },
                        "directories": {
                        },
                        "rename": {
                        }
                    },
                    "linux": {
                        "files": {
                        },
                        "directories": {
                        },
                        "rename": {
                        }
                    }
                }
                j = json.dumps(settings_template, sort_keys=True, indent=4, separators=(',', ': '))
                f.write(j + "\n")
        except:
            file_errors.append(settings_file)

    return file_errors


def run_backup_thread(force=False):
    if not running_thread:
        t = BackupOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()


def copy_file(src, dest):
    status = False
    try:
        shutil.copyfile(src, dest)
        print "OS Specific User Files: SUCCESS - Copied to User: %s" % src
    except:
        print "OS Specific User Files: ERROR - Could not copy file: %d" % src
        status = True
    return status


def copy_directory(src, dest):
    status = False
    try:
        if os.path.exists(dest):
            print "OS Specific User Files: REMOVING - Directory already exists: %s" % dest
            shutil.rmtree(dest)
    except:
        print "OS Specific User Files: ERROR - Could not remove: %s" % dest
        status = True
        return status

    try:
        shutil.copytree(src, dest)
        print "OS Specific User Files: SUCCESS - Copied to User: %s" % src
    except:
        print "OS Specific User Files: ERROR - Could not copy directory: %d" % src
        status = True
    return status


def move_files(src, dest):
    status = False
    if os.path.exists(dest):
        if os.path.isdir(dest):
            try:
                if os.path.exists(dest):
                    print "OS Specific User Files: REMOVING - Directory already exists: %s" % dest
                    shutil.rmtree(dest)
            except:
                print "OS Specific User Files: ERROR - Could not remove: %s" % dest
                status = True
                return status
        else:
            try:
                print "OS Specific User Files: REMOVING - File already exists: %s" % dest
                os.remove(dest)
            except:
                print "OS Specific User Files: ERROR - Could not remove: %s" % dest
                status = True
                return status
    try:
        shutil.move(src, dest)
    except:
        print "OS Specific User Files: ERROR - Could not move %s" % src
        status = True
    return status


def make_dir(directory):
    error = False
    try:
        os.makedirs(directory)
        print "OS Specific User Files: ERROR - Successfully created directory: %s" % directory
    except:
        print "OS Specific User Files: ERROR - Could not create directory: %s" % directory
        error = True
    return error


class OsUserFiles(threading.Thread):
    def __init__(self, file_list, force=False):
        self.force = force
        self.file_list = file_list
        threading.Thread.__init__(self)

    def copy_all(self):
        pass

    def run(self):
        global running_thread
        running_thread = True
        self.copy_all()
        running_thread = False


class BackupOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def copy_all(self):
        errors = False
        # Copy single files
        for item in self.file_list['files']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['files'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(user, value)

            if os.path.exists(src):
                errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['directories'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(user, value)

            if os.path.exists(src):
                errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['rename'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(ospath, value)

            if os.path.exists(src):
                errors |= move_files(src, dest)

        if errors:
            os_specific_alert()


class CopyOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def copy_all(self):
        errors = False
        # Copy single files
        for item in self.file_list['files']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['files'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['directories'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['rename'][item])
            src = os.path.join(user, key)
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src):
                errors |= move_files(src, dest)

        if errors:
            os_specific_alert()


class BackupOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print "OS Specific User Files: Backing up User to OsSpecificUserFiles..."
        run_backup_thread(force=True)


class CopyOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print "OS Specific User Files: Copying files to User..."
        run_copy_thread(force=True)


# Setup
print "OS Specific User Files: Checking if setup is required..."
file_errors = setup()
if len(file_errors) > 0:
    for f in file_errors:
        print "OS Specific User Files: Could setup file or directory: %s" % f
    os_specific_alert()
else:
    # Setup success; enable running the backup/copy threads when invoked
    running_thread = False

    # Load settings
    ossettings = sublime.load_settings(settings)

    # Run copy thread, but only copy if file is not already present
    print "OS Specific User Files: Checking for files that have never been copied over..."
    run_copy_thread(force=False)
