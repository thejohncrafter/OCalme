
# OCalme : Outil de Compilation Avancé pour Langage Machine
##### (mais En fait c'est du python)

Un exemple de programme est contenu dans "example.oklm".
Essayez :

 - "python3 main.py example.oklm"
 - "python3 main.py -h" pour obtenir de l'aide.
 - "python3 main.py example.oklm --norun --gen" pour avoir le code généré
  sans exécuter le programme.

Les types de donnés représentant l'AST et l'IR sont tous équipés d'une fonction
"pretty" qui est faite pour générer des messages à la fois lisibles et
reflétant les données contenues par la structure sur laquelle elle a été
appelée.
Les options "--ast" et "--ir" de "main.py" utilisent cette fonction pour
afficher les structures de données générées.

Le compilateur est séparé en plusieurs "étages" :
On récupère le programme dans le fichier donné en argument (sous forme de
chaîne de caractères), puis on effectue les étapes suivantes :

 - Parsing :
   C'est la construction de l'AST ("Abstract Syntax Tree").
   Les fichiers contenant les algorithmes sont "parse_util.py", "parseBlock.py",
   "parseFunction.py", "parseLRValue.py", "PrecedenceBuilder.py"
   et "Tokenizer.py".
   Les définitions des types de données de l'AST sont dans "AST.py".
   Le principe général est qu'un fichier OCalme est structuré en :
   - fonctions ("parseFunction.py")
     - représentées par leurs paramètres et un bloc de code :
     - blocs ("parseBlock.py")
       contiennent des commandes (assignements, ou simplement des calculs)
       - commandes: Les commandes sont composées d'éventuellement un symbole
         spécial (le symbole "=", pour l'assignement), et de :
         - lvalues: Ce sont les valeurs qui peuvent se trouver à gauche dans
           une égalité, c'est à dire des variables ou des n-uplets.
         - rvalues: Les valeurs qui peuvent se troubver à droite d'un symbole
           "=". Les variables et les n-uplets sont bien sûr des rvalues, mais
           aussi les structures "if", "loop" et "if unwrap"; et les blocs de
           code.
         le fichier concerné est "parseLRValue".
         L'algorithme contenu dans ce fichier est en fait capable de parser
         des lvalues _et_ des rvalues. En fait, les lvalues sont des cas
         particuliers de rvalues (ce sont les rvalues uniquement composées
         de variables et de n-uplets de lvalues).
 - Flattening :
   Une fois que l'AST a été construit, on peut générer une représentation
   intermédiaire ("IR", "Intermediate Representation") qui est plus facile
   à manipuler par un programme (le but étant que la transpilation vers
   Python soit triviale).
   On profite de cette étape pour vérifier que le programme est bien typé.
   Remarque : Il semble, d'après la taille du fichier "flattener.py" et la
   complexité des algorithmes qu'il contient, qu'il aurait été plus sage de
   réserver la vérification des types pour une autre étape de la compilation.
 - Transpilation :
   On transforme l'IR en un programme Python. L'algorithme est dans
   "transpile.py". Il est assez simple, et montre comment utiliser les
   structures de données générées par le Flattener.
