#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <pwd.h>
#include <sys/wait.h>
#include <signal.h>
#include <readline/readline.h>
#include <readline/history.h>
#include "util.h"
#include <pwd.h>
#include <sys/utsname.h>
#include "colors.h"
#include "libc_like.h"

#define handle_error(msg) \
do { perror(msg); exit(EXIT_FAILURE); } while (0)

#define BUFFER 512

/* ------------ Déclarations --------------- */

/* Alias Structure. */
typedef struct Alias {
    int inFile;
    char command[30];
    char alias[30];
} Alias;

// PROCESSUS EN ARRIERE-PLAN STRUCTURE
typedef struct bg_cmd
{
    int id;
    pid_t pid;
    char *cmd;
	struct bg_cmd *next;
} bg_cmd;


static bg_cmd* bg_list = NULL; 

// passer a 1 pour obtenir des informations de DEBUG
int DEBUG = 0;

// Pid de minishell
pid_t minishell_pid;
pid_t minishell_pgid;
int minishell_terminal;

int active_bgs = 0; //Nombre de backgrounds qui est en cours d'exécution

// Supprimer un un processus en arrière-plan après avoir fini
int del_bg(int pid, int *status_term){
    active_bgs--;
    if(bg_list->pid == pid && bg_list->next == NULL){
		printf("\n[%d]+  Fini\t   %s\n", bg_list->id, bg_list->cmd);
        bg_list = NULL;
        return 1;
    }

    bg_cmd *prev_cmd, *temp;

    if(bg_list->pid == pid){
        temp = bg_list;
        bg_list = bg_list->next;
		printf("\n[%d]+  Fini\t   %s\n", temp->id, temp->cmd);
        free(temp);
        return 1;
    }
    temp = bg_list->next;
    prev_cmd = bg_list;
    while (temp != NULL)
    {
        if(temp->pid == pid)
        {
            prev_cmd->next = temp->next;
			printf("\n[%d]+  Fini\t   %s\n", temp->id, temp->cmd);
            free(temp);
            return 1;
        }
        temp = temp->next;
    }
    return 0;
}

/* ------------ gestionnaires de signal --------------- */

void ctrlC(int sig)
{
	if(sig == SIGINT)
	{
		//printf("get pid: %d\n", getpid());
		if(getpid() != minishell_pid)
			kill(getpid(), SIGKILL);
		else
			printf("\n");
	}
}

void ctrlZ(int sigg)
{
	if(sigg == SIGTSTP)
	{
		//printf("get pid: %d\n", getpid());
		if(getpid() != minishell_pid)
			kill(getpid(), SIGTSTP);
		else
			printf("\n");
	}
}

// gestionnaire de processus en arrière-plan
void bg_handler(int signum)
{
    int ppid = -1;
    static int status_term;
    if((ppid = waitpid(-1, &status_term, WNOHANG)) > 0)
        del_bg(ppid, &status_term);
}


static char *line_cmd = (char *)NULL;
char minishell_msg[BUFFER];

/* ------------ Définition de fonctions --------------- */


/** 
* @brief La fonction récupère les alias du fichier et les dépose dans des structures
* @return un tableau de structures d'alias 
*/
Alias * file_to_alias_structs(void)
{
    /* Declarations */
	int i;
    int file_descriptor;
	Alias * Alias_array;
    int buf_size = 512; // Max number of char to read
    char * content;
    char * command;
	char * save_ptr;
	char * save_ptr2;
	char delimiter = '\n';
	char delimiter2 = '=';

    /* Allocation */
    if ((content = calloc(buf_size, 1)) == NULL) {
        handle_error("calloc");
    }
	if ((command = calloc(buf_size, 1)) == NULL) {
        handle_error("calloc");
    }

    /* Open file 
	* If it doesn't succeed, will return a blank structure with default values
	*/
    if ((file_descriptor = open(".aliases", O_RDONLY)) == -1) {
		Alias blank_alias;
		blank_alias.inFile = 1;	
		strcpy_like(blank_alias.command, "*****"); 
		strcpy_like(blank_alias.alias, "*****");

		if ((Alias_array = calloc(1, sizeof(Alias))) == NULL)
		{
			handle_error("calloc");
		}

		Alias_array[0] = blank_alias;
		free(content);
		free(command);
      	return Alias_array;
    }
    
    /* Read and store to content string */
    if ((read(file_descriptor, content, buf_size)) == -1 ) {
        handle_error("read");
    }

	/* Create an array of 100 aliases */
	if ((Alias_array = calloc(100, sizeof(Alias))) == NULL)
	{
		handle_error("calloc");
	}

	/* Parse the content into the structures */
	content = strtok_r_like(content, delimiter, &save_ptr); // content has the line, and save_ptr the rest of data
	command = strtok_r_like(content, delimiter2, &save_ptr2); // command has the command in line and save_ptr2 the alias
	strcpy_like(Alias_array[0].command, command);
	strcpy_like(Alias_array[0].alias, save_ptr2);
	i = 1;
	while (content != NULL)
	{
		content = strtok_r_like(NULL, delimiter, &save_ptr); // retrieve the line
		

		if (content == NULL)
		{
			break;
		}
		command = strtok_r_like(content, delimiter2, &save_ptr2);
		strcpy_like(Alias_array[i].command, command);
		strcpy_like(Alias_array[i].alias, save_ptr2);
		Alias_array[i].inFile = 1;
		i++;
	}

	close(file_descriptor);
	return Alias_array;
}

/**
 * @brief La fonction recherche si l'alias existe dans le tableau d'alias 
 * @param Alias_array le tableau d'alias à analyser
 * @param alias l'alias qui servira à trouver la commande
 * @return l'offset de la commande dans le tableau d'alias, sinon retourne -1
 */
int search_alias(Alias * Alias_array, char * alias)
{
	for (int i = 0; Alias_array[i].command[0] != '\0'; i++)
	{
		if (!strcmp_like(Alias_array[i].alias, alias))
		{
			//printf("%s is an alias of %s in index %d.\n", alias, Alias_array[i].command, i);
			return i;
		}
	}
	return -1;
}


/*
 * Fonction qui émule la commande history linux-like
 * @return void : affichage de l'historique
 */ 
void show_history()
{
    HIST_ENTRY **list_hist;
    int i = history_base;
	int j = 0;

    list_hist = history_list ();
    
	while(list_hist[j]){
		printf ("%d: %s\n", i, list_hist[j]->line);
		++j;
		++i;
	}
}

// La commande jobs
void print_jobs(){
    bg_cmd *bg = bg_list;
    if (bg == NULL)
        return;

    while (bg != NULL){
        printf("[%d]+ %2d En cours d'exécution  %3s\n", bg->id, bg->pid, bg->cmd);
        bg = bg->next;
    }
    //printf("\n");
}

int fd_stdout = STDOUT_FILENO;
int fd_stderr = STDERR_FILENO;

void run_here_document(char *word, int fd){
	int c, t;
	char *chaine;
	do {
		chaine = malloc((BUFFER-1) * sizeof(char));
		c = getchar();
		t = scanf("%s", chaine);
		
		if (strcmp_like(chaine, word) == 0){
			write(fd, word, strlen(word));
			write(fd, "\n", 1);
			break;
		}
		write(fd, (char *)&c, strlen((char*)&c));
		write(fd, chaine, strlen(chaine));
		//write(fd, "\n", 1);
        
	} while(t > 0);
	//dup2(fd, fd_stdout);
}


/**
 * @brief Lit multiple commandes sur l'entrée standard
 * @param commands multiple commandes à exécuter
 * @param line_cmd liste des commandes
 * @return nombre de commmandes dans la ligne
 */ 
int read_command(struct cmd commands[]){
	int i=0, j=1;
	char *p;
	int is_cmd = 1;
	int is_bg = 0;

	char *line = malloc(BUFFER);

	if (line_cmd){
        free(line_cmd);
        line_cmd = (char *)NULL;
    }
	//printf("%s", minishell_msg);
	line_cmd = readline(minishell_msg);
	//line_cmd = readline(minishell_msg);
	line_cmd = strip_spaces(line_cmd);

	if(strlen(line_cmd) == 0){
		return 0;
	}

	//Ajouter la commande dans l'histoire
	add_history(line_cmd);
	strcpy_like(line, line_cmd);

	p = strtok(line_cmd, " ");
								
	//lire les arguments
	while(p != NULL) {
		if(is_bg){
			printf("minishell : & devrait être utilisé à la fin de la commande\n");
			return 0;
		}
		
		//Si c'est une commande, et c'est pas la redirection et pipe
		if (is_cmd)
		{

			if (strcmp_like(p, "exit") == 0) {
				return -1;
			}
			if (strcmp_like(p,"cd")==0)
			{
				commands[i].is_cd = 1;
			}
			if (strcmp_like(p,"export")==0)
			{
				commands[i].is_exp = 1;
			}

			strcpy_like(commands[i].command, p);
			is_cmd = 0;
			//i++;
			p = strtok (NULL, " ");

		} else {
			// Lire le symbole de la redirection et de pipe
			if (strcmp_like(p, ">")==0) {
				//lire le fichier de sortie et le stocker dans fdest et écraser le contenu
				//scanf("%s",tmp);
				p = strtok (NULL, " ");
				strcpy_like(commands[i].fdest_out, p);
				commands[i].is_truncated = 1;
				commands[i].is_out = 1;
			}
			else if (strcmp_like(p, ">>") == 0){
				//lire le fichier de sortie et le stocker dans fdest et n'écraser pas le contenu
				//scanf("%s",tmp);
				p = strtok (NULL, " ");
				strcpy_like(commands[i].fdest_out, p);
				commands[i].is_truncated = 0;
				commands[i].is_out = 1;
			}
			else if (strcmp_like(p, "2>") == 0){
				//lire le fichier de sortie et rediriger les erreurs de syntaxe, le flux "stderr" vers un fichier
				//écraser le contenu
				//scanf("%s",tmp);
				p = strtok (NULL, " ");
				strcpy_like(commands[i].fdest_err, p);
				commands[i].is_truncated = 1;
				commands[i].is_err = 1;
			}
			else if (strcmp_like(p, "2>>") == 0){
				//lire le fichier de sortie et rediriger les erreurs de syntaxe, le flux "stderr" vers un fichier
				//n'écraser pas le contenu
				//scanf("%s",tmp);
				p = strtok (NULL, " ");
				strcpy_like(commands[i].fdest_err, p);
				commands[i].is_truncated = 0;
				commands[i].is_err = 1;
			} 
			else if (strcmp_like(p, "<") == 0){
				p = strtok (NULL, " ");
				if (strcmp_like(commands[i].args[1], "") != 0)
				{
					commands[i].is_or = 1;
					strcpy_like(commands[i].args[j], commands[i].args[1]);
					strcpy_like(commands[i].args[1], p);
					commands[i].nbArgs++;
					is_cmd = 1;
					break;
				}
			}
			else if (strcmp_like(p, "<<") == 0){
				commands[i].is_here = 1;
						
				char *pathy = malloc(BUFFER);
				strcpy_like(pathy, getMyDirectory());
				strcat(pathy, "/");
				strcat(pathy, "tmp_pipe");
				
				if (strcmp_like(commands[i].args[1], "") != 0){
					strcpy_like(commands[i].args[j], commands[i].args[1]);
					strcpy_like(commands[i].args[1], pathy);
					free(pathy);
				}
				else{
					strcpy_like(commands[i].args[1], pathy);
				}
				j++;
				

				p = strtok (NULL, " ");
				
				strcpy_like(commands[i].args[j], p);
				//printf("Paramètre in here strcpy %s %s\n", commands[i].args[j - 1], commands[i].args[j]);
				commands[i].nbArgs = j - 1;
			}
			// Si c'est une pipe 
			else if (strcmp_like(p, "|") == 0){
				is_cmd = 1;
				commands[i].is_tmp = 1;
				i++;
				char pathy[BUFFER];
				strcpy_like(pathy, getMyDirectory());
				strcat(pathy, "/");
				strcat(pathy, "tmp_pipe");
				strcpy_like(commands[i].args[1], pathy);
				commands[i].nbArgs++;
				j=2;
			}
			// Si c'est un opérateur AND
			else if (strcmp_like(p, "&&") == 0){
				is_cmd = 1;
				commands[i].is_and = 1;
				i++;
				j=1;
			}
			// Si c'est un opérateur OR
			else if (strcmp_like(p, "||") == 0){
				is_cmd = 1;
				commands[i].is_or = 1;
				i++;
				j=1;
			}
			else if (strcmp_like(p, "&") == 0){
				is_cmd = 0;
				is_bg = 1;
				active_bgs++;
				commands[i].is_bg = 1;

				if(bg_list == NULL){
					bg_list = malloc(sizeof(bg_cmd));
					bg_list->cmd = malloc(sizeof(BUFFER));
					bg_list->next = NULL;
					strcpy_like(bg_list->cmd, line);
					free(line);
					bg_list->id = active_bgs;
				}
				else{
					bg_cmd *temp = bg_list;
					while (temp->next != NULL){
						temp = temp->next;
					}
					temp->next = malloc(sizeof(bg_cmd));
					temp->next->cmd = malloc(sizeof(BUFFER));
					strcpy_like(temp->next->cmd, line);
					free(line);
					temp->next->id = active_bgs;
					temp->next->next = NULL;
				}
				//i++;
			}
			else{

				strcpy_like(commands[i].args[j], p);
				commands[i].nbArgs++;
				j++;
			}
			p = strtok (NULL, " ");
		}
	}
	i++;
	//printf("Nombre de commands est %d\n", i);
	return i;
}

/**
 * @brief Exécuter multiple commandes sur l'entrée standard
 * @param command commande à exécuter
 * @param cmd chemin absolu vers le fichier exécutable de la commande
 * @param args nombre d'arguments de la commande
 * @return 1 si l'exécution réussit, 0 sinon
 */ 
int run_command(char* cmd, char* args[], struct cmd* command) {
	pid_t pid;
	int status = 0;
	int fd_out = -1, fd_err = -1, fd_tmp = -1;

	pid = fork();
	switch (pid) {
		case -1:
			perror("Creation processus");
			return EXIT_FAILURE;
		case 0:
			//signal(SIGCHLD, &bg_handler);

			if(command->is_out || command->is_err || command->is_tmp) {
				//Si la redirection est > ou >>
				if(command->is_truncated) {
					if (command->is_out)
					{
						fd_out = open(command->fdest_out, O_WRONLY | O_CREAT | O_TRUNC, 0666);
					}
					if (command->is_err) {
						fd_err = open(command->fdest_err, O_WRONLY | O_CREAT | O_TRUNC, 0666);
					} 
					
				}
				// Si la redirection est >>, 2>>
				else
				{
					if (command->is_out)
					{
						fd_out = open(command->fdest_out, O_WRONLY | O_CREAT | O_APPEND , 0666);
					} 
					if (command->is_err) {
						fd_err = open(command->fdest_err, O_WRONLY | O_CREAT | O_APPEND , 0666);
					}
				}
				// Si c'est une pipe
				if(command->is_tmp) {
					fd_tmp = open("tmp_pipe", O_WRONLY | O_CREAT | O_TRUNC, 0666);
				}

				if(fd_out == -1 && fd_tmp == -1 && fd_err == -1) {
					perror("Erreur : ");
					return EXIT_FAILURE;
				}
				// redirection de sortie
				if (fd_out != -1)
				{
					dup2(fd_out, fd_stdout);
					
				}

				//Redirection d'erreur
				if (fd_err != -1)
				{
					dup2(fd_err, fd_stderr);
				}

				// Redirection de pipe
				if (fd_tmp != -1)
				{
					dup2(fd_tmp, fd_stdout);
					dup2(fd_tmp, fd_stderr);
				}	
			}
			if(command->is_here){
				fd_tmp = open("tmp_pipe", O_WRONLY | O_CREAT | O_TRUNC, 0666);
				if(fd_tmp == -1) {
					perror("Erreur : ");
					return EXIT_FAILURE;
				}
				run_here_document(command->args[command->nbArgs + 1], fd_tmp);
			}
			//Si c'est un processus en arrière-plan
			if(command->is_bg){
				bg_cmd *temp = bg_list;
				
				while (temp->next != NULL){
					temp = temp->next;
				}
				int bg_pid = fork();
				if(bg_pid < 0){
					perror("Exécuter le processus en arrière-plan");
					exit(EXIT_FAILURE);
				}
				if(bg_pid == 0){
					if(execv(cmd, args) == -1) {
						printf("minishell : %s : commande introuvable\n", command->command);
						//perror("Erreur execv: ");
						exit(EXIT_FAILURE);
					}
				}
				else{
					//int pid = bg_pid + 1;
					temp->pid = bg_pid;
					printf("[%d] %d\n", temp->id, bg_pid);

					signal(SIGCHLD, &bg_handler);
				}
			}
			else{
				//utilisation de execv pour exécuter la commande
				if (execv(cmd, args) == -1) {
					printf("minishell : %s : commande introuvable\n", command->command);
					//perror("Erreur execv: ");
					exit(EXIT_FAILURE);
				}

				//attente de la fin de la commande
				waitpid(pid, &status, WUNTRACED);
				if(WIFSTOPPED(status) && WSTOPSIG(status))	{
					return EXIT_SUCCESS;
				}
				if (WIFEXITED(status)) {
					return WEXITSTATUS(status);
				}
				return EXIT_FAILURE;

			}

			//Fermer les descripteurs
			if (fd_out != -1)
			{
				close(fd_out);
			}
			if (fd_err != -1)
			{
				close(fd_err);
			}
			if (fd_tmp != -1)
			{
				close(fd_tmp);
			}
			return EXIT_SUCCESS;

		default:
			//attente de la fin de la commande
			waitpid(pid, &status, WUNTRACED);

			if (command->nbArgs > 0)
			{
				char fullname[BUFFER];
				strcpy_like(fullname, args[1]);
				char* name = theFileName(args[1]);
				if (strcmp_like(name, "tmp_pipe") == 0 )
				{
					unlink(fullname);
				}
				free(name);
			}
			if(WIFSTOPPED(status) && WSTOPSIG(status))	{
				return EXIT_SUCCESS;
			}
			if (WIFEXITED(status)) {
				return WEXITSTATUS(status);
			}
			return EXIT_FAILURE;
	}
}


/* ------------ Main Processus --------------- */

int main(int argc, char ** argv) {
	minishell_pid = getpid();
	minishell_pgid = getpgrp();
	minishell_terminal = STDIN_FILENO;
	tcsetpgrp(minishell_terminal, minishell_pgid);

	/* Initialize an array of aliases and retrieve the content of the .aliases file */

	Alias * aliases;
	aliases = file_to_alias_structs();
	
	
	signal(SIGINT, &ctrlC);
	signal(SIGTSTP, &ctrlZ);

	char* currentpath = (char*) malloc(BUFFER);
    char* currentpath2 = (char*) malloc(BUFFER);
	
	strcpy_like(currentpath, getMyDirectory());
	//char line_cmd[BUFFER];

	struct passwd *user;
	struct utsname node;
	clearScreen();


	if(argc > 1)
		DEBUG=1;
	while(1) {

		aliases = file_to_alias_structs(); //update the alias struct to reflect new changes
		
		struct cmd* commands = malloc(256 * sizeof(struct cmd));
        strcpy_like(currentpath2, getMyDirectory());
		char* args[BUFFER];
		// Afficher minishell
		if ((user = getpwuid(getuid())) == NULL){
			perror("Getpwuid");
			exit(EXIT_FAILURE);	
    	}
		if(uname(&node) == -1){
			perror("Uname");
			exit(EXIT_FAILURE);
		}
                
		char *fullname = (char*) malloc(BUFFER);
		strcpy_like(fullname, theFileName(currentpath2));
		//printf("%s",currentpath);
		//char* folder = theFileName(fullname);
		//free(folder);
		sprintf(minishell_msg, YELLOW "%s@%s" RESET BLUE " --" RESET RED "minishell ~ " CYAN "%s" RESET  BLUE " > " RESET, user->pw_name, node.nodename, fullname);
		free(fullname);
		//on récupère la ligne commande a exécuter
		int i = read_command(commands);
		if(i == 0){
			//printf("\n");
			continue;
		}

		if(i == -1) {
			free(currentpath);
			free(commands);
			printf("Exit\n");
			exit(EXIT_SUCCESS);
			return 1;
		}

		for (int p = 0; p < i; ++p)
		{
			int index_alias;

			index_alias = search_alias(aliases, commands[p].command);

			
			if (index_alias != -1) // if the command is an alias
			{
				strcpy_like(commands[p].args[0], aliases[index_alias].command);
				//call function with argument: aliases[index_alias].command		
			} else {
				strcpy_like(commands[p].args[0], commands[p].command);
			}
			int ret = 1;

			int j = 0;
			
			for (j = 0; j < commands[p].nbArgs + 1; ++j)
			{
				args[j] = commands[p].args[j];
			}
			args[j] = NULL;

			if (commands[p].is_cd) //If cd is called
			{
				ret = !cd(commands[p].nbArgs+1, args);
				// commands[p].is_cd = 0;
			}
			else if (!strcmp_like(commands[p].args[0], "clear") || (!strcmp_like(commands[p].args[0], "cls")) )  // If clear in first argument 
			{
				clearScreen();
				ret = 1;
			}
			else if (strcmp_like(commands[p].args[0], "history") == 0) {
					show_history();
					ret = 1;
			}

			else if (strcmp_like(commands[p].args[0], "jobs") == 0) {
					print_jobs();
					ret = 1;
			}
			else if (commands[p].is_exp) //If export is called
			{
				ret = !export_env(commands[p].nbArgs+1, args);
				commands[p].is_exp = 0;
			}
			else { // Call function in file
				char pathToexec[BUFFER];
				strcpy_like(pathToexec, currentpath);
				strcat(pathToexec, "/");
				strcat(pathToexec, commands[p].args[0]);
				
				ret = !run_command(pathToexec, args, &commands[p]);
				/*if((returnValue = )){
					if(DEBUG) printf("===> commande executée avec erreur\n");
				}else{
					if(DEBUG) printf("===> commande executée sans erreur\n");
				}*/
				
			}
			if (!(commands[p].is_and && ret) && (!commands[p].is_or))
			{
				int t = p;
				while(t<i)	{
					if (commands[t].is_and)
					{
						p++;
					}
					if (commands[t].is_or)
					{
						break;
					}
					t++;
				}
			}
		}
		free(commands);
	}
	free(currentpath);
	free(currentpath2);
	return EXIT_SUCCESS;
}