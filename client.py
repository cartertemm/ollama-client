import threading
import wx
from ollama import Client
from accessible_output2.outputs import auto


default_host = "localhost"
default_port = "11434"
auto_output = auto.Auto()


def speak(text, interrupt=True, *args, **kwargs):
	auto_output.speak(text, interrupt=interrupt, *args, **kwargs)


class ConfigDialog(wx.Dialog):
	def __init__(self, parent, title):
		super(ConfigDialog, self).__init__(parent, title=title, size=(250, 200))
		
		self.panel = wx.Panel(self)
		self.vbox = wx.BoxSizer(wx.VERTICAL)
		
		# Host configuration
		self.host_lbl = wx.StaticText(self.panel, label="Host:")
		self.host_txt = wx.TextCtrl(self.panel, value=default_host)
		self.vbox.Add(self.host_lbl, flag=wx.LEFT | wx.TOP, border=10)
		self.vbox.Add(self.host_txt, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
		
		# Port configuration
		self.port_lbl = wx.StaticText(self.panel, label="Port:")
		self.port_txt = wx.TextCtrl(self.panel, value=default_port)
		self.vbox.Add(self.port_lbl, flag=wx.LEFT | wx.TOP, border=10)
		self.vbox.Add(self.port_txt, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

		# Buttons
		self.ok_button = wx.Button(self.panel, label='OK')
		self.cancel_button = wx.Button(self.panel, label='Cancel')
		self.buttons = wx.StdDialogButtonSizer()
		self.buttons.AddButton(self.ok_button)
		self.buttons.AddButton(self.cancel_button)
		self.buttons.Realize()

		self.vbox.Add(self.buttons, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
		
		self.panel.SetSizer(self.vbox)

		self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
		self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

	def on_ok(self, event):
		self.EndModal(wx.ID_OK)

	def on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)

	def get_host_port(self):
		return self.host_txt.GetValue(), int(self.port_txt.GetValue())

class AIChatApp(wx.Frame):
	def __init__(self, parent, title):
		super(AIChatApp, self).__init__(parent, title=title, size=(400, 300))

		self.original_title = title

		dialog = ConfigDialog(None, 'Server Configuration')
		if dialog.ShowModal() == wx.ID_OK:
			host, port = dialog.get_host_port()
			self.ollama = Client(f"{host}:{port}")
		else:
			self.Close(True)
		dialog.Destroy()

		# Prompt for initial model selection
		self.current_model = None
		self.prompt_for_model()

		self.messages = []
		self.streaming = False
		self.speech_buffer = ""

		self.InitUI()
		self.Centre()

	def prompt_for_model(self):
		model_dialog = ModelManagerDialog(self, "Select Model", self.ollama)
		if model_dialog.ShowModal() == wx.ID_OK and model_dialog.selected_model:
			self.current_model = model_dialog.selected_model
			self.update_title()
		else:
			self.Close(True)  # Close the app if no model is selected
		model_dialog.Destroy()

	def update_title(self):
		self.SetTitle(f"{self.current_model} - {self.original_title}")

	def InitUI(self):
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)
		history_label = wx.StaticText(panel, label="Message History:")
		vbox.Add(history_label, flag=wx.LEFT | wx.TOP, border=10)
		self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
		vbox.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		message_label = wx.StaticText(panel, label="Enter Your Message:")
		vbox.Add(message_label, flag=wx.LEFT, border=10)
		self.input_txt = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
		self.input_txt.SetFocus()
		vbox.Add(self.input_txt, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
		role_label = wx.StaticText(panel, label="Role:")
		vbox.Add(role_label, flag=wx.LEFT | wx.TOP, border=10)
		self.role_choice = wx.Choice(panel, choices=["User", "Assistant", "System"])
		self.role_choice.SetSelection(0)  # Default to 'User'
		vbox.Add(self.role_choice, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
		hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Options button
		self.options_button = wx.Button(panel, label='Options')
		self.options_button.Bind(wx.EVT_BUTTON, self.OnOptions)
		hbox_buttons.Add(self.options_button, flag=wx.RIGHT, border=5)
		# Send button
		self.send_button = wx.Button(panel, label='Send')
		self.send_button.Bind(wx.EVT_BUTTON, self.OnSend)
		self.input_txt.Bind(wx.EVT_TEXT_ENTER, self.OnSend)
		hbox_buttons.Add(self.send_button, flag=wx.RIGHT, border=5)
		self.model_button = wx.Button(panel, label='Manage Models (Ctrl+M)')
		self.model_button.SetAcceleratorTable(wx.AcceleratorTable([
			(wx.ACCEL_CTRL, ord('M'), self.model_button.GetId())
		]))
		self.model_button.Bind(wx.EVT_BUTTON, self.OnManageModels)
		hbox_buttons.Add(self.model_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
		vbox.Add(hbox_buttons, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
		panel.SetSizerAndFit

	def OnManageModels(self, event):
		dialog = ModelManagerDialog(self, "Manage Models", self.ollama, self.current_model)
		if dialog.ShowModal() == wx.ID_OK:
			self.current_model = dialog.selected_model
			self.update_title()
		dialog.Destroy()

	def OnSend(self, event):
		user_input = self.input_txt.GetValue()
		if user_input:
			self.input_txt.SetValue("")
			threading.Thread(target=self.stream_response, args=[user_input]).start()

	def OnOptions(self, event):
		popup_menu = wx.Menu()
		clear_item = popup_menu.Append(wx.ID_ANY, "&Clear Conversation")
		self.Bind(wx.EVT_MENU, self.OnClearConversation, clear_item)
		save_item = popup_menu.Append(wx.ID_ANY, "Save Output to File")
		self.Bind(wx.EVT_MENU, self.OnSaveOutput, save_item)
		self.PopupMenu(popup_menu, self.options_button.GetPosition())
		popup_menu.Destroy()

	def OnClearConversation(self, event):
		self.messages = []
		self.text_ctrl.Clear()

	def OnSaveOutput(self, event):
		with wx.FileDialog(self, "Save text", wildcard="Text files (*.txt)|*.txt", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return	 # the user changed their mind

			# Save the content of the text control to the file
			pathname = fileDialog.GetPath()
			try:
				with open(pathname, 'w') as file:
					file.write(self.text_ctrl.GetValue())
			except IOError as exc:
				print(exc)  # for now

	def stream_response(self, user_input):
		role = self.role_choice.GetStringSelection().lower()
		self.messages.append({"role": role, "content": user_input})
		prefix = self.get_prefix_for_role(role)
		self.append_to_output(prefix+user_input+"\n")
		response = self.ollama.chat(model=self.current_model, messages=self.messages, stream=True)
		self.streaming = True
		output = ""
		for chunk in response:
			if "error" in chunk:
				self.text_ctrl.AppendText("AI: error, "+chunk["error"]+"\n")
				break
			if chunk.get("done") is False:
				message = chunk["message"]
				content = message["content"]
				if not output:
					self.append_to_output(self.get_prefix_for_role(message["role"]))
				output += content
				self.append_to_output(content)
			elif chunk.get("done", False):
				self.messages.append({"role": "assistant", "content": output})
				self.append_to_output("\n")
		self.streaming = False
		self.speak_output()  # there might still be text in the buffer we need to announce

	def append_to_output(self, text, suppress_announcement=False):
		self.text_ctrl.AppendText(text)
		if not suppress_announcement:
			if not self.streaming:
				speak(text)
				return
			if len(self.speech_buffer.split(" ")) >= 10:
				self.speak_output()
				self.speech_buffer = ""
			self.speech_buffer += text

	def speak_output(self):
		if self.speech_buffer:
			speak(self.speech_buffer, interrupt=False)

	def get_prefix_for_role(self, role):
		if role == "user":
			return "You: "
		elif role == "assistant":
			return "AI: "
		elif role == "system":
			return "System: "

class ModelManagerDialog(wx.Dialog):
	def __init__(self, parent, title, client, current_model=None):
		super(ModelManagerDialog, self).__init__(parent, title=title, size=(500, 400))
		self.client = client
		self.selected_model = current_model
		
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)
		
		self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.list_ctrl.InsertColumn(0, "Name", width=140)
		self.list_ctrl.InsertColumn(1, "Model", width=140)
		self.list_ctrl.InsertColumn(2, "Size", width=100)
		self.list_ctrl.InsertColumn(3, "Last Modified", width=120)
		
		self.load_models()
		
		vbox.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		
		self.ok_button = wx.Button(panel, label='OK')
		self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
		vbox.Add(self.ok_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
		
		panel.SetSizer(vbox)

	def load_models(self):
		models = self.client.list()
		models = models.get("models", [])
		for model in models:
			index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), model['name'])
			self.list_ctrl.SetItem(index, 0, model['name'])
			self.list_ctrl.SetItem(index, 1, model['model'])
			self.list_ctrl.SetItem(index, 2, str(model['size']))
			self.list_ctrl.SetItem(index, 3, model['modified_at'])
			if model['name'] == self.selected_model:
				self.list_ctrl.Focus(index)
				self.list_ctrl.Select(index)

	def on_ok(self, event):
		selection = self.list_ctrl.GetFirstSelected()
		if selection != -1:
			self.selected_model = self.list_ctrl.GetItemText(selection, 0)
		self.EndModal(wx.ID_OK)


def main():
	app = wx.App()
	ex = AIChatApp(None, title='Simple AI Chat')
	ex.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
