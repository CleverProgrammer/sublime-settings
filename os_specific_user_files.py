import sublime
import sublime_plugin
import os
import shutil
import threading

ossettings = sublime.load_settings('os_specific_user_files.sublime-settings')
osplatform = sublime.platform()
user = os.path.join(sublime.packages_path(), 'User')
ospath = os.path.join(user, 'OsSpecificUserFiles', osplatform)
running_thread = False


def run_copy_thread(force=False):
    if not running_thread:
        t = CopyOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()


def copy_file(src, dest):
    try:
        shutil.copyfile(src, dest)
    except:
        print "Could not copy file: %d" % src


def copy_directory(src, dest):
    try:
        if os.path.exists(dest):
            print "Directory already exists: %s" % dest
            print "Removing directory before copy"
            shutil.rmtree(dest)
    except:
        print "Could not remove: %s" % dest
        return

    try:
        shutil.copytree(src, dest)
    except:
        print "Could not copy directory: %d" % src


def move_files(src, dest):
    if os.path.exists(dest):
        if os.path.isdir(dest):
            try:
                if os.path.exists(dest):
                    print "Directory already exists: %s" % dest
                    print "Removing directory before move"
                    shutil.rmtree(dest)
            except:
                print "Could not remove: %s" % dest
                return
            shutil.move(src, dest)
        else:
            try:
                print "File already exists: %s" % dest
                print "Removing file before move"
                os.remove(dest)
            except:
                print "Could not remove: %s" % dest
                return

    try:
        shutil.move(src, dest)
    except:
        print "Could not move %s" % src


class CopyOsUserFiles(threading.Thread):
    def __init__(self, file_list, force=False):
        self.force = force
        self.file_list = file_list
        threading.Thread.__init__(self)

    def run(self):
        global running_thread
        running_thread = True
        self.copy_all()
        running_thread = False

    def copy_all(self):
        # Copy single files
        for item in self.file_list['files']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['files'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(dest_dir, key)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['directories'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(dest_dir, key)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['rename'][item])
            src = os.path.join(user, key)
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src):
                move_files(src, dest)


class CopyOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        run_copy_thread(force=True)


run_copy_thread(force=False)
