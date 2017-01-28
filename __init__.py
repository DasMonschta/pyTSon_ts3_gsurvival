from ts3plugin import ts3plugin
import ts3defines, os.path
import ts3lib as ts3
from ts3lib import getPluginPath
from os import path
from PythonQt.QtSql import QSqlDatabase
from PythonQt.QtGui import *
from pytsonui import *


class Gsurvival(ts3plugin):
    name = "Gsurvival"
    requestAutoload = False
    version = "1.0"
    apiVersion = 21
    author = "Luemmel"
    description = "Ein Survivalpaket fuer den drecks Gomme TS."
    offersConfigure = True
    commandKeyword = ""
    infoTitle = None
    hotkeys = []
    menuItems = [(ts3defines.PluginMenuType.PLUGIN_MENU_TYPE_GLOBAL, 0, "GSurvival Einstellungen", "")]

    dlg = None
    gommeuid = "QTRtPmYiSKpMS8Oyd4hyztcvLqU="

    directory = path.join(getPluginPath(), "pyTSon", "scripts", "gsurvival")

    def __init__(self):
        # Database connect
        self.db = QSqlDatabase.addDatabase("QSQLITE", "pyTSon_gsurvival")
        self.db.setDatabaseName(path.join(self.directory, "gsurvival.db"))
        if not self.db.isValid():
            raise Exception("Database invalid")
        if not self.db.open():
            raise Exception("Could not open database.")

        self.db_c = QSqlDatabase.addDatabase("QSQLITE","pyTSon_contacts")
        self.db_c.setDatabaseName(ts3.getConfigPath() + "settings.db")
        if not self.db_c.isValid():
            raise Exception("Datenbank ungueltig")
        if not self.db_c.open():
            raise Exception("Datenbank konnte nicht geoeffnet werden")

        s = self.db.exec_("SELECT * FROM settings")
        if s.next():
            self.friend_o = bool(s.value("friend_o_active"))
            self.friend_tp = bool(s.value("friend_tp_active"))
            self.friend_m = bool(s.value("friend_msg_active"))
            self.friend_msg = str(s.value("friend_msg"))
            self.block_cb = bool(s.value("block_cb_active"))
            self.block_m = bool(s.value("block_msg_active"))
            self.block_msg = str(s.value("block_msg"))
            self.kick = bool(s.value("kick_active"))
            self.kick_option = bool(s.value("kick_option_active"))
            self.kick_m = bool(s.value("kick_msg_active"))
            self.kick_msg = str(s.value("kick_msg"))
            self.whitelist = bool(s.value("whitelist_active"))

    def stop(self):
        self.db.close()
        self.db.delete()
        self.db_c.close()
        self.db_c.delete()
        QSqlDatabase.removeDatabase("pyTSon_gsurvival")
        QSqlDatabase.removeDatabase("pyTSon_contacts")


    def configure(self, qParentWidget):
        try:
            if not self.dlg: self.dlg = SettingsDialog(self)
            self.dlg.show()
            self.dlg.raise_()
            self.dlg.activateWindow()
        except:
            try:
                from traceback import format_exc; ts3.logMessage(format_exc(), ts3defines.LogLevel.LogLevel_ERROR, "PyTSon Script", 0)
            except:
                try:
                     from traceback import format_exc; print(format_exc())
                except:
                    print("Unknown Error")

    def onMenuItemEvent(self, sch_id, a_type, menu_item_id, selected_item_id):
        if a_type == ts3defines.PluginMenuType.PLUGIN_MENU_TYPE_GLOBAL:
            if menu_item_id == 0:
                if not self.dlg: self.dlg = SettingsDialog(self)
                self.dlg.show()
                self.dlg.raise_()
                self.dlg.activateWindow()

    def contactStatus(self, uid):
        q = self.db_c.exec_("SELECT * FROM contacts WHERE value LIKE '%%IDS=%s%%'" % uid)
        ret = 2
        if q.next():
            val = q.value("value")
            for l in val.split('\n'):
                if l.startswith('Friend='):
                    ret = int(l[-1])
        q.delete()
        return ret

    def onClientMoveEvent(self, schid, clientID, oldChannelID, newChannelID, visibility, moveMessage):
        (error, suid) = ts3.getServerVariableAsString(schid, ts3defines.VirtualServerProperties.VIRTUALSERVER_UNIQUE_IDENTIFIER)
        if suid == self.gommeuid and (self.friend_o or self.friend_tp or self.block_cb):
            (error, myid) = ts3.getClientID(schid)
            (error, mych) = ts3.getChannelOfClient(schid, myid)
            if newChannelID == mych:
                (error, uid) = ts3.getClientVariableAsString(schid, clientID, ts3defines.ClientProperties.CLIENT_UNIQUE_IDENTIFIER)
                f = self.contactStatus(uid)
                (error, gid) = ts3.getClientVariableAsInt(schid, clientID, ts3defines.ClientPropertiesRare.CLIENT_CHANNEL_GROUP_ID)
                (error, mygid) = ts3.getClientVariableAsInt(schid, myid, ts3defines.ClientPropertiesRare.CLIENT_CHANNEL_GROUP_ID)
                # Block Bann
                if f == 1 and self.block_cb and (mygid == 10 or mygid == 11):
                    (error, dbid) = ts3.getClientVariableAsUInt64(schid, clientID, ts3defines.ClientPropertiesRare.CLIENT_DATABASE_ID)
                    ts3.requestSetClientChannelGroup(schid, [12], [mych], [dbid])
                    if self.block_m:
                        ts3.requestSendPrivateTextMsg(schid, self.block_msg, clientID)
                # Freund O
                if f == 0 and self.friend_o and mygid == 10 and not gid == 11:
                    (error, dbid) = ts3.getClientVariableAsUInt64(schid, clientID, ts3defines.ClientPropertiesRare.CLIENT_DATABASE_ID)
                    ts3.requestSetClientChannelGroup(schid, [11], [mych], [dbid])
                    if self.friend_m:
                        ts3.requestSendPrivateTextMsg(schid, self.friend_msg, clientID)

                # Freund TP
                if f == 0 and self.friend_tp and (myid == 10 or mygid == 11):
                    (error, tp) = ts3.getChannelVariableAsInt(schid, mych, ts3defines.ChannelPropertiesRare.CHANNEL_NEEDED_TALK_POWER)
                    (error, sgid) = ts3.getClientVariableAsInt(schid, clientID, ts3defines.ClientPropertiesRare.CLIENT_SERVERGROUPS)

                    if tp > 3 and not sgid == 0:
                        if tp > 3 and gid == 9:
                            # gast
                            ts3.requestClientSetIsTalker(schid, clientID, True)
                        elif tp > 25 and gid == 10:
                            # Channel Admin
                            ts3.requestClientSetIsTalker(schid, clientID, True)
                        elif tp > 23 and gid == 11:
                            # Operator
                            ts3.requestClientSetIsTalker(schid, clientID, True)
                        elif tp > 5 and sgid == 13:
                            # Registriert
                            ts3.requestClientSetIsTalker(schid, clientID, True)
                        elif tp > 10 and sgid == 14:
                            # premiuem
                            ts3.requestClientSetIsTalker(schid, clientID, True)
                        elif tp > 15 and sgid == 30:
                            # premiuem +
                            ts3.requestClientSetIsTalker(schid, clientID, True)


    def onClientChannelGroupChangedEvent(self, schid, channelGroupID, channelID, clientID, invokerClientID, invokerName, invokerUniqueIdentity):
        (error, suid) = ts3.getServerVariableAsString(schid, ts3defines.VirtualServerProperties.VIRTUALSERVER_UNIQUE_IDENTIFIER)
        if self.kick and suid == self.gommeuid:
            (error, myid) = ts3.getClientID(schid)
            (error, mych) = ts3.getChannelOfClient(schid, myid)
            (error, mygid) = ts3.getClientVariableAsInt(schid, myid, ts3defines.ClientPropertiesRare.CLIENT_CHANNEL_GROUP_ID)
            if self.kick_option:
                if myid == invokerClientID:
                    if mych == channelID and channelGroupID == 12 and (mygid == 10 or mygid == 11):
                        ts3.requestClientKickFromChannel(schid, clientID, "")
                        if self.kick_m:
                            ts3.requestSendPrivateTextMsg(schid, self.kick_msg, clientID)
            else:
                if mych == channelID and channelGroupID == 12 and (mygid == 10 or mygid == 11):
                    ts3.requestClientKickFromChannel(schid, clientID, "")
                    if self.kick_m:
                        ts3.requestSendPrivateTextMsg(schid, self.kick_msg, clientID)

class SettingsDialog(QDialog):
    try:
        def __init__(self, gsurvival, parent=None):
            try:
                self.gs = gsurvival
                super(QDialog, self).__init__(parent)
                setupUi(self, os.path.join(getPluginPath(), "pyTSon", "scripts", "gsurvival", "gsurvival.ui"))
                self.setWindowTitle("Gsurvival by Luemmel")
                # self.btn_add_domain.clicked.connect(self.add_domain)
                self.btn_anwenden.clicked.connect(self.save_changes)

                self.pixmap = QPixmap(os.path.join(getPluginPath(), "pyTSon", "scripts", "gsurvival", "gsurvival.png"))
                self.label_logo.setPixmap(self.pixmap)

                self.cb_friend_o.setChecked(self.gs.friend_o)
                self.cb_friend_tp.setChecked(self.gs.friend_tp)
                self.cb_friend_msg.setChecked(self.gs.friend_m)
                self.input_friend.setText(self.gs.friend_msg)

                self.cb_block_cb.setChecked(self.gs.block_cb)
                self.cb_block_msg.setChecked(self.gs.block_m)
                self.input_block.setText(self.gs.block_msg)

                self.cb_kick.setChecked(self.gs.kick)
                self.cb_kick_option.setChecked(self.gs.kick_option)
                self.cb_kick_msg.setChecked(self.gs.kick_m)
                self.input_kick.setText(self.gs.kick_msg)
            except:
                try:
                    from traceback import format_exc; ts3.logMessage(format_exc(), ts3defines.LogLevel.LogLevel_ERROR, "PyTSon Script", 0)
                except:
                    try:
                         from traceback import format_exc; print(format_exc())
                    except:
                        print("Unknown Error")

        def save_changes(self):
            # Friend
            self.gs.friend_o = self.cb_friend_o.isChecked()
            self.gs.friend_tp = self.cb_friend_tp.isChecked()
            self.gs.friend_m = self.cb_friend_msg.isChecked()
            self.gs.friend_msg = self.input_friend.toPlainText()
            # Block
            self.gs.block_cb = self.cb_block_cb.isChecked()
            self.gs.block_m = self.cb_block_msg.isChecked()
            self.gs.block_msg = self.input_block.toPlainText()
            # Autokick
            self.gs.kick = self.cb_kick.isChecked()
            self.gs.kick_option = self.cb_kick_option.isChecked()
            self.gs.kick_m = self.cb_kick_msg.isChecked()
            self.gs.kick_msg = self.input_kick.toPlainText()

            self.gs.db.exec_("UPDATE settings SET ""friend_o_active = "+str(int(self.gs.friend_o))+", "
                             "friend_tp_active = "+str(int(self.gs.friend_tp))+", "
                             "friend_msg_active = "+str(int(self.gs.friend_m))+", "
                             "friend_msg = '"+self.gs.friend_msg+"', "
                             "block_cb_active = "+str(int(self.gs.block_cb))+", "
                             "block_msg_active = "+str(int(self.gs.block_m))+", "
                             "block_msg = '"+self.gs.block_msg+"', "
                             "kick_active = "+str(int(self.gs.kick))+", "
                             "kick_option_active = "+str(int(self.gs.kick_option))+", "
                             "kick_msg_active = "+str(int(self.gs.kick_m))+", "
                             "kick_msg = '"+self.gs.kick_msg+"'")

            ts3.printMessageToCurrentTab("[[b]Gsurvival[/b]] Die Einstellungen wurden gespeichert.")
    except:
        try:
            from traceback import format_exc; ts3.logMessage(format_exc(), ts3defines.LogLevel.LogLevel_ERROR, "PyTSon Script", 0)
        except:
            try:
                from traceback import format_exc;  print(format_exc())
            except:
                print("Unknown Error")

