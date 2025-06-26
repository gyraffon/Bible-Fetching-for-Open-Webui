# Bible-Fetching-for-Open-Webui
Bible Fetching Tool and citations French/English
==>
1 : launch the python script in the venv open-webui
the database bible must be created
2: import the json file in open-webui
3: set the function settings (place of the db : it must be the same that the venv of open-webui.

MAJ 26/06/2025
Reste à diffuser auprès de la communauté, à commenter

Le tool permet de chercher dans la bible à partir de certains mots clé en français ou en anglais, les mots traduits en anglais (si français), recherche dans la bible.db (en anglais) contenant toutes les bibles, puis traduit le résultat en français et en enfin le renvoit au llm quui l'insère dans le prompt en tant que citation. Si le prommpt était en anglais la rtéponse est faite en anglais également.
La seconde, le script python sert à créer la db. Il doit être lancé dans le même venv que open-webui avec le terminal.

The tool makes it possible to search in the Bible from certain key words in French or English, translated them into English (if French), searches in the bible.db (in english) containing all the Bibles, then translates the result into French (if initially french) and finally the reference to the prompt as a quotation.
The second, the python script is to create the db. It must be launch in the same venv of open-webui with terminal.
