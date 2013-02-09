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


Documentation:

About:
OS Specific User Files was created to make backing up a common User directories for different OS platforms.  I back mine up on Github.
Once you have every thing setup, you can simply clone your your User directory from github, and all of your backed up OS specific files or directories
will be copied over.  If you update the repository from a different system, you can simply fetch the changes later on the other system, and then
execute the copy command to copy the new settings over your old ones.  You can define additional files or remove files from your settings at any time
as well.  If you remove a file or directory from the settings file, and they exist in the backup folder, you can clean the with the
"Clean Orphaned Backup Files" command.

Installation:
- Drop os_specific_user_files.py into Packages/User.
- Plugin will automatically create a settings file and the directories to store OS specific files in.
- Add the following commands to Default.sublime-commands:

    // Force Copy OS Specific User files
    {
        "caption": "Os Specific User Files: Update User Files",
        "command": "copy_os_user_files"
    },
    // Force Backup OS Specific User Files
    {
        "caption": "Os Specific User Files: Backup User Files",
        "command": "backup_os_user_files"
    },
    // Clean Orphaned Backup Files
    {
        "caption": "Os Specific User Files: Clean Orphaned Backup Files",
        "command": "clean_orphaned_os_user_files"
    },

- Define the files you want to backup for your specific OS platform in the auto-generated os_specific_user_files.sublime-settings.
    Example: windows setup (Backed up file or folder name is the key on the left.  File or folder name the file known as under User is the value
             on the left).  If you would like to rename any file buried in a directory after copying, you can list the files under the "rename"
             section. This is particularly useful for menu files that are seen by sublime no matter how deep they are buried in directories.
             The same naming convention follows for rename: backed up file -> user file.

        "windows": {
            "files": {
                "Package Control.sublime-settings": "Package Control.sublime-settings",
                "Terminal.sublime-settings": "Terminal.sublime-settings",
                "Preferences.sublime-settings": "Preferences.sublime-settings"
            },
            "directories": {
                "SideBarEnhancements": "SideBarEnhancements"
            },
            "rename": {
                "SideBarEnhancements/Open With/Side Bar.sublime-menu.json": "SideBarEnhancements/Open With/Side Bar.sublime-menu"
            }
        },

Usage:
- Every time Sublime Text is started, the plugin will check if any of your defined files that are backed up are missing from User.
  It will copy them if they are missing. It will also backup defined files that exist in User but are missing in back up.
- At any time you backup all defined files wiht the "Backup User Files" you added to the Command Palette.  This will copy over all backeup files.
- At any time you can copy all of your backup files over your current user files using the "Update User Files" command you added in the Command Palette.
- At any time you can clean up all orphaned files in the backup directory (files that are no longer defined in the settings file, but exist in
  the backup directory) by using the "Clean Orphaned Backup Files" command you added to the Command Palette.
"""

import sublime
import sublime_plugin
import os
import shutil
import threading
import json
from glob import glob


def os_specific_alert():
    sublime.error_message('OS Specific User Files encountered one or more errors.\nPlease see the console for more info.')


def os_specific_info(text):
    sublime.set_timeout(lambda: sublime.status_message('OS Specific User Files: ' + text), 100)


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


def queue_thread(t):
    if running_thread:
        sublime.set_timeout(lambda: queue_thread(t), 3000)
    else:
        t()


def run_orphan_thread(force=True):
    if not running_thread:
        t = CleanOrphanedFiles(ossettings.get(osplatform, {}), force)
        t.start()
        MonitorThread(t)


def run_copy_thread(force=False):
    if not running_thread:
        t = CopyOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()
        MonitorThread(t)


def run_backup_thread(force=False):
    if not running_thread:
        t = BackupOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()
        MonitorThread(t)


def copy_file(src, dest):
    status = False
    try:
        shutil.copyfile(src, dest)
        print("OS Specific User Files: SUCCESS - Copied to User: %s" % src)
    except:
        print("OS Specific User Files: ERROR - Could not copy file: %d" % src)
        status = True
    return status


def copy_directory(src, dest):
    status = False
    try:
        if os.path.exists(dest):
            print("OS Specific User Files: REMOVING - Directory already exists: %s" % dest)
            shutil.rmtree(dest)
    except:
        print("OS Specific User Files: ERROR - Could not remove: %s" % dest)
        status = True
        return status

    try:
        shutil.copytree(src, dest)
        print("OS Specific User Files: SUCCESS - Copied to User: %s" % src)
    except:
        print("OS Specific User Files: ERROR - Could not copy directory: %d" % src)
        status = True
    return status


def move_files(src, dest):
    status = False
    if os.path.exists(dest):
        if os.path.isdir(dest):
            try:
                if os.path.exists(dest):
                    print("OS Specific User Files: REMOVING - Directory already exists: %s" % dest)
                    shutil.rmtree(dest)
            except:
                print("OS Specific User Files: ERROR - Could not remove: %s" % dest)
                status = True
                return status
        else:
            try:
                print("OS Specific User Files: REMOVING - File already exists: %s" % dest)
                os.remove(dest)
            except:
                print("OS Specific User Files: ERROR - Could not remove: %s" % dest)
                status = True
                return status
    try:
        shutil.move(src, dest)
    except:
        print("OS Specific User Files: ERROR - Could not move %s" % src)
        status = True
    return status


def make_dir(directory):
    error = False
    try:
        os.makedirs(directory)
        print("OS Specific User Files: ERROR - Successfully created directory: %s" % directory)
    except:
        print("OS Specific User Files: ERROR - Could not create directory: %s" % directory)
        error = True
    return error


class MonitorThread():
    def __init__(self, t):
        self.thread = t
        self.status_pos = 0
        self.direction = 1
        self.max_status = 5
        sublime.set_timeout(lambda: self.__start_monitor(), 0)

    def __start_monitor(self):
        sublime.status_message("OS Specific User Files: Busy - [>" + "-" * self.max_status + "]")
        sublime.set_timeout(lambda: self.__monitor(), 500)

    def __monitor(self):
        if self.thread.is_alive():
            if self.direction > 0:
                if self.status_pos < self.max_status:
                    self.status_pos += 1
                else:
                    self.direction = -1
            else:
                if self.status_pos > 0:
                    self.status_pos -= 1
                else:
                    self.direction = 1

            indicator = ">" if self.direction > 0 else "<"

            leftover = 5 - self.status_pos
            sublime.status_message("OS Specific User Files: Busy - [" + "-" * self.status_pos + indicator + "-" * leftover + "]")
            sublime.set_timeout(self.__monitor, 1)
        else:
            sublime.set_timeout(self.thread.on_complete, 500)


class OsUserFiles(threading.Thread):
    errors = False
    completion_msg = ""

    def __init__(self, file_list, force=False):
        self.force = force
        self.file_list = file_list
        threading.Thread.__init__(self)

    def on_complete(self):
        if self.errors:
            os_specific_alert()
        else:
            os_specific_info(self.completion_msg)

    def apply(self):
        pass

    def run(self):
        global running_thread
        running_thread = True
        self.apply()
        running_thread = False


class CleanOrphanedFiles(OsUserFiles):
    def __init(self, file_list, force=True):
        OsUserFiles.__init__(self, file_list, True)

    def apply(self):
        self.errors = False
        count = 0
        ospaths = [
            os.path.join(plugin_storage, 'linux'),
            os.path.join(plugin_storage, 'windows'),
            os.path.join(plugin_storage, 'osx')
        ]

        # Search all OS folders
        for os_folder in ospaths:
            print("OS Specific User Files: SEARCHING - OS folder: %s" % os_folder)
            for item in glob(os.path.join(os_folder, "*")):
                directories = []
                files = []
                if os.path.isdir(item):
                    directories.append(item)
                else:
                    files.append(item)

                # Search for orphaned files
                for found_file in files:
                    found = False
                    for item in self.file_list['files']:
                        reported_file = os.path.normpath(os.path.join(os_folder, item))
                        if reported_file == found_file:
                            found = True
                            break
                    if not found:
                        try:
                            print("OS Specific User Files: REMOVING - Orphaned file: %s" % found_file)
                            os.remove(found_file)
                            count += 1
                        except:
                            print("OS Specific User Files: ERROR - Could not remove: %s" % found_file)
                            self.errors |= True

                # Search for orphaned directories
                for found_dir in directories:
                    found = False
                    for item in self.file_list['directories']:
                        reported_dir = os.path.normpath(os.path.join(os_folder, item))
                        if reported_dir == found_dir:
                            found = True
                            break
                    if not found:
                        try:
                            print("OS Specific User Files: REMOVING - Orphaned directory: %s" % found_dir)
                            shutil.rmtree(found_dir)
                            count += 1
                        except Exception as e:
                            print (e)
                            print ("OS Specific User Files: ERROR - Could not remove: %s" % found_dir)
                            self.errors |= True

        if not self.errors:
            self.completion_msg = str(count) + ' orphaned files/directories removed successfully!' if count > 0 else 'No orphaned files/directories found!'


class BackupOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def apply(self):
        count = 0
        self.errors = False
        # Copy single files
        for item in self.file_list['files']:
            dest = os.path.normpath(os.path.join(ospath, item))
            dest_dir = os.path.dirname(dest)
            src = os.path.normpath(os.path.join(user, self.file_list['files'][item]))

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                count += 1
                self.errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            dest = os.path.normpath(os.path.join(ospath, item))
            dest_dir = os.path.dirname(dest)
            src = os.path.normpath(os.path.join(user, self.file_list['directories'][item]))

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                count += 1
                self.errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            dest = os.path.normpath(os.path.join(ospath, item))
            dest_dir = os.path.dirname(dest)
            src = os.path.normpath(os.path.join(ospath, self.file_list['rename'][item]))

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                count += 1
                self.errors |= move_files(src, dest)

        if not self.errors:
            self.completion_msg = str(count) + ' targets backed up successfully!' if count > 0 else 'No backup required!'


class CopyOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def apply(self):
        count = 0
        self.errors = False
        # Copy single files
        for item in self.file_list['files']:
            src = os.path.normpath(os.path.join(ospath, item))
            dest = os.path.normpath(os.path.join(user, self.file_list['files'][item]))
            dest_dir = os.path.dirname(dest)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                count += 1
                self.errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            src = os.path.normpath(os.path.join(ospath, item))
            dest = os.path.normpath(os.path.join(user, self.file_list['directories'][item]))
            dest_dir = os.path.dirname(dest)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                count += 1
                self.errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            src = os.path.normpath(os.path.join(user, item))
            dest = os.path.normpath(os.path.join(user, self.file_list['rename'][item]))

            if (not os.path.exists(dest) or self.force) and os.path.exists(src):
                count += 1
                self.errors |= move_files(src, dest)

        if not self.errors:
            self.completion_msg = str(count) + ' targets copied successfully!' if count > 0 else 'No copy required!'


class CleanOrphanedOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print("OS Specific User Files: Searching for orphaned backed up files...")
        run_orphan_thread(force=True)


class BackupOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print("OS Specific User Files: Backing up User to OsSpecificUserFiles...")
        run_backup_thread(force=True)


class CopyOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print("OS Specific User Files: Copying files to User...")
        run_copy_thread(force=True)


def plugin_loaded():
    global osplatform
    global user
    global plugin_storage
    global ospath
    global settings
    global running_thread
    global ossettings

    osplatform = sublime.platform()
    user = os.path.join(sublime.packages_path(), 'User')
    plugin_storage = os.path.join(user, 'OsSpecificUserFiles')
    ospath = os.path.join(plugin_storage, osplatform)
    settings = 'os_specific_user_files.sublime-settings'
    running_thread = True

    # Setup
    print("OS Specific User Files: Checking if setup is required...")
    file_errors = setup()
    if len(file_errors) > 0:
        for f in file_errors:
            print("OS Specific User Files: Could not setup file or directory: %s" % f)
        os_specific_alert()
    else:
        # Setup success; enable running the backup/copy threads when invoked
        running_thread = False

        # Load settings
        ossettings = sublime.load_settings(settings)

        # Run copy thread, but only copy if file is not already present
        print("OS Specific User Files: Checking for files that have never been copied over...")
        run_copy_thread(force=False)

        # Run backup thread, but only copy if file is not already backed up
        print("OS Specific User Files: Checking for files that have never been backed up...")
        queue_thread(lambda: run_backup_thread(force=False))
