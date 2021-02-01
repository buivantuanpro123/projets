/**
 * @file Discussion.cpp
 * @brief Definition des methodes de la classe Discussion.
 * @author EthicsLab (Alexandre Giard, Arnaud Fevrier, Matthieu Le Gallic, et Van Tuan Bui)
 *
 * Fichier qui contient le code des methodes de la classe Discussion.
 * Voir commentaire des methodes dans le .h
 */

#define AES_ACTIVE 1
#include "Discussion.h"

int Discussion::recv_s(SOCKET s, char* buf, int len, int flags) {
#if AES_ACTIVE == 1
	printf("||Receive size: %i\n", len);
	DWORD crypt_size = 0;
	int result = recv(s, (char*)&crypt_size, sizeof(DWORD), MSG_WAITALL);
	printf("|||Crypt size: %i\n", crypt_size);
	if (result > 0) {
		printf("||Try to receive\n");
		char* cryptToReceive = (char*)malloc(sizeof(char) * crypt_size);
		recv(s, cryptToReceive, crypt_size, MSG_WAITALL);
		printf("|||Message recv: %32s\n", cryptToReceive);
		CryptDecrypt(m_clef, NULL, TRUE, 0, (BYTE*)cryptToReceive, &crypt_size);
		memcpy(buf, cryptToReceive, len);
		printf("|||Message recv: %32s\n", buf);
		free(cryptToReceive);
		return 1;
	}
	else {
		return 0;
	}
#else
	return recv(s, buf, len, MSG_WAITALL);
#endif	
}

int Discussion::send_s(SOCKET s, const char* buf, int len, int flags) {
#if AES_ACTIVE == 1
	printf("||Send size: %i\n", len);
	DWORD longueurBlocTexte = 0;
	CryptEncrypt(m_clef, NULL, TRUE, 0, NULL, &longueurBlocTexte, 0);
	double longueurTemp = (static_cast <double> (len)) / (static_cast <double> (longueurBlocTexte));
	DWORD crypt_size = longueurBlocTexte + (longueurBlocTexte * (static_cast <unsigned int> (floor(longueurTemp))));
	printf("|||Send Crypt Size: %i\n", crypt_size);
	char* cryptToSend = (char*)malloc(sizeof(char) * crypt_size);
	memset(cryptToSend, ' ', crypt_size);
	memcpy(cryptToSend, buf, len);
	printf("||||Message send: %32s\n", cryptToSend);

	CryptEncrypt(m_clef, 0, TRUE, 0, (BYTE*)cryptToSend, (DWORD*)&len, crypt_size);
	printf("||||Message send: %32s\n", cryptToSend);
	send(s, (char*)&crypt_size, sizeof(DWORD), 0);
	send(s, cryptToSend, crypt_size, 0);
	free(cryptToSend);
	return 1;
#else
	return send(s, buf, len, flags);
#endif
}

// From https://stackoverflow.com/questions/440133/how-do-i-create-a-random-alpha-numeric-string-in-c
void gen_random(char *s, const int len) {
	srand(time(NULL));
	static const char alphanum[] =
		"0123456789"
		"abcdefghijkmnopqrstuvwxyz";
	for (int i = 0; i < len; ++i) {
		s[i] = alphanum[rand() % (sizeof(alphanum) - 1)];
	}
	s[len] = 0;
}


Participant Discussion::getParticipantFromSocket(SOCKET sock) {
	for (Participant p : m_participants) {
		if (p.get_socket() == sock)
			return p;
	}
	SOCKADDR_IN sockaddr_in;
	Participant p;

	int size = sizeof(sockaddr_in);
	getsockname(sock, (struct sockaddr*) & sockaddr_in, &size);
	if (inet_ntop(AF_INET, &(sockaddr_in.sin_addr.s_addr), p.get_ip(), IP_LENGTH) == 0) {
		printf("Erreur: inet_ntop %i\n", WSAGetLastError());
	};
	inet_ntop(AF_INET, &(sockaddr_in.sin_addr.s_addr), p.get_ip(), IP_LENGTH);
	sprintf_s(p.get_port(), PORT_LENGTH, "%d", ntohs(sockaddr_in.sin_port));
	p.set_socket(sock);
	return p;
}

std::vector<Participant> Discussion::getParticipantsList() {
	return m_participants;
}

//on récupère le participant qui a la vue maximale
Participant Discussion::getMaxP_Participants() {
	int max = 0;
	Participant p_max;
	for (Participant p : m_participants) {
		if (max < p.get_numP()) {
			max = p.get_numP();
			p_max = p;
		}
	}
	return p_max;
}

Discussion::Discussion() {
	//Network settings - Define the WinSock version
	WSADATA WSAData;
	int err = WSAStartup(MAKEWORD(2, 2), &WSAData);
	if (err != 0) {
		// Tell the user that we could not find a usable
		// Winsock DLL.                                  
		printf("WSAStartup failed with error: %d\n", err);
		exit(1);
	}
	// Initalisation
	FD_ZERO(&m_descriptor_users);

	//Génération de l'identifiant unique de conversation
	gen_random(m_id, 5-1);
	// Génération de la clé pour le transfert de données AES
	CryptAcquireContext(&m_cryptographicServiceProvider, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT);
	HCRYPTHASH hHash;
	CryptCreateHash(m_cryptographicServiceProvider, CALG_SHA_256, 0, 0, &hHash);
	CryptHashData(hHash, (BYTE*)m_id, sizeof(m_id), 0);
	CryptDeriveKey(m_cryptographicServiceProvider, CALG_AES_128, hHash, 0, &m_clef);

	//Recupération de l'ensemble des interfaces de l'utilisateur
	this->setUserInterfacesIPs();
}

bool Discussion::initInvitationLink(Participant p, const char* id) {
	
	//Définie l'id de conversation et regénérère le hash
	strcpy_s(m_id, id);
	CryptAcquireContext(&m_cryptographicServiceProvider, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT);
	HCRYPTHASH hHash;
	CryptCreateHash(m_cryptographicServiceProvider, CALG_SHA_256, 0, 0, &hHash);
	CryptHashData(hHash, (BYTE*)m_id, sizeof(m_id), 0);
	CryptDeriveKey(m_cryptographicServiceProvider, CALG_AES_128, hHash, 0, &m_clef);

	// On se connecte au lien d'invitation et on demande la réception des adresses IP de la discussion
	//
	Participant distant = addUser(p); //On demande la connexion à l'utilisateur
	if (strcmp(distant.get_ip(), "0.0.0.0") == 0) {
		return false;
	}
	init();
	requestInfoParticipant(distant); // Requête de toutes les IP
	requestMessagesParticipant(distant); //Requête de tous les messages

	//Turn on For loop
	stopping = false;
	m_listenThread = std::thread(&Discussion::whileListen, this);
	return true;
}

void Discussion::initNewDiscussion(char title[TITLE_LENGTH]) {
	// On devient le propriétaire de toute la discussion
	memset(m_owner, true, sizeof(m_owner));

	// Création d'une nouvelle discussion
	//
	strcpy(m_discussion_title, title);

	// Aucun participant pour le moment, donc on attend sur le listen
	init();

	//Turn on For loop
	stopping = false;
	m_listenThread = std::thread(&Discussion::whileListen, this);
}


void Discussion::init() {
	// Création du descripteur d'écoute
	if (m_participantMy.set_socket(socket(AF_INET, SOCK_STREAM, 0)), m_participantMy.get_socket() == 0) {
		perror("Socket error");
		exit(EXIT_FAILURE);
	}

	//-------------- Définition de l'adresse d'écoute (On écoute sur tous les interfaces sur un port disponible)
	SOCKADDR_IN address_serveur;
	address_serveur.sin_family = AF_INET;
	inet_pton(AF_INET, m_participantMy.get_ip(), &(address_serveur.sin_addr.s_addr));
	address_serveur.sin_port = htons(0); //Le port est définie par le système d'exploitation
	//--------------

	// Bind du descripteur selon les paramètres addr donné
	if (bind(m_participantMy.get_socket(), (struct sockaddr*) & address_serveur, sizeof(address_serveur)) < 0) {
		perror("Bind error");
		exit(EXIT_FAILURE);
	}

	// On définie le descripteur en écoute. 
	if (listen(m_participantMy.get_socket(), 5) < 0) {
		perror("Listen error");
		exit(EXIT_FAILURE);
	}

	Participant tmp_port = getParticipantFromSocket(m_participantMy.get_socket());
	m_participantMy.set_port(tmp_port.get_port()); //On définie le port d'invitation de notre Participation

		// (- Partie optionnel pour l'affichage console -)
	printf("---------------------------------\n(Invite key is: %s:%s)\n---------------------------------\n", m_participantMy.get_ip(), m_participantMy.get_port());

	//On rajoute le descripteur d'écoute au liste de socket d'écoute
	FD_SET(m_participantMy.get_socket(), &m_descriptor_users);
}

void Discussion::whileListen() {
	fd_set fd_users_to_read = m_descriptor_users;
	TIMEVAL time = { 0, 100000 }; //Wait 100ms and enter in the while (check if the discussion stopping)
	while (select(FD_SETSIZE, &fd_users_to_read, NULL, NULL, &time) >= 0) {
		if (stopping) {
			//L'ensemble des sockets sont contenue dans m_descriptor_users
			for (u_int i = 0; i < m_descriptor_users.fd_count; i++) {
				closesocket(fd_users_to_read.fd_array[i]);
			}
			//On return la fonction, le thread se ferme
			return;
		}
		for (u_int i = 0; i < fd_users_to_read.fd_count; i++) {
			SOCKET descripter_toread = fd_users_to_read.fd_array[i];
			if (descripter_toread == m_participantMy.get_socket()) {

				// Un nouveau client se connecte!
				// On le rajoute à la liste des participants à la conversation
				Participant new_client;
				SOCKADDR_IN address_new; //Variable temporaire
				int size = sizeof(address_new);
				new_client.set_socket(accept(m_participantMy.get_socket(), (SOCKADDR*)&address_new, (socklen_t*)&size));
				if (new_client.get_socket() < 0) {
					perror("!!Accept client error");
					exit(EXIT_FAILURE);
				}
				if (inet_ntop(AF_INET, &(address_new.sin_addr.s_addr), new_client.get_ip(), IP_LENGTH) == 0) {
					printf("Erreur: inet_ntop %i\n", WSAGetLastError());
				};
				sprintf_s(new_client.get_port(), PORT_LENGTH, "%d", ntohs(address_new.sin_port));

				//Affichage de la connexion sur la console
				printf("(Connection from %s:%s)\n", new_client.get_ip(), new_client.get_port());

				// On rajoute la nouvelle connexion à la liste des participants
				FD_SET(new_client.get_socket(), &m_descriptor_users);
			}
			else {

				//Des données sont reçus
				printf(">Lecture du header\n");
				int read_size;
				headerPDU head;
				if (read_size = recv_s(descripter_toread, (char*)(&head), sizeof(head), 0), read_size > 0) {
					if (head.type == 'I') {
						printf(">>Lecture du header IPs\n");
						recv_s(descripter_toread, m_discussion_title, TITLE_LENGTH, 0);
						printf(">>>Titre recu: %s\n", m_discussion_title);
						printf(">>>Taille recu: %i\n", head.len);
						printf(">>>Donc nombre d'IP: %i\n", (head.len / (int)sizeof(Participant)));
						std::vector<Participant> participants;
						for (int i = 0; i < (head.len / (int)sizeof(Participant)); i++) {
							Participant new_user;
							recv_s(descripter_toread, (char*)(&new_user), sizeof(new_user), 0);
							printf(">>>>Client recu: %s:%s:%d\n", new_user.get_ip(), new_user.get_port(), new_user.get_numP());
							new_user.set_socket(descripter_toread);
							participants.push_back(addUser(new_user)); //On ajoute le participant et on envoie un paquet d'information comme quoi on est nouveau participant
						}

						//Pour mettre à jour le nombre de participants après d'avoir connecté à tous les participants reçus
						for (Participant p : participants) {
							infoParticipant(p);
						}
						printf(">>Fin de lecture du header IPs\n");
					}
					else if (head.type == 'J') {
						printf(">>Lecture du header REQUEST IPs\n");
						Participant new_user;
						recv_s(descripter_toread, (char*)(&new_user), sizeof(new_user), 0);
						printf(">>>Avec l'ip recu: %s:%s\n", new_user.get_ip(), new_user.get_port());
						new_user.set_socket(descripter_toread);
						new_user.set_numP(min((int)m_participants.size() + 1, MAX_CONNECTIONS )); //car on envoie tous les participants

						while (m_participants.size() >= MAX_CONNECTIONS) {
							//std::cout << "Le nombre de participant is " << m_participants.size() << std::endl;
							Participant p = getMaxP_Participants();
							std::cout << "Supprimer le participant " << p.get_port() << std::endl;
							FD_CLR(p.get_socket(), &m_descriptor_users);
							removeUser(p);
							closesocket(p.get_socket());
							m_participantMy.dec_NumP();
						}

						m_participants.push_back(new_user);
						m_participantMy.inc_NumP();

						//On informe les autres participants d'un nouveau participant qui vient d'entrer
						headerPDU head;
						head.type = 'C'; //Comme Changé
						head.len = (int)sizeof(Participant);
						for (Participant p : m_participants) {
							send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
							send_s(p.get_socket(), (char*)&m_participantMy, sizeof(m_participantMy), 0);
						}

						// On envoit la liste des IP
						sendMParticipants(new_user);
					}
					else if (head.type == 'F') {
						printf(">>Lecture du header INFO ADD IP\n");
						Participant new_user;
						recv_s(descripter_toread, (char*)(&new_user), sizeof(new_user), 0);
						printf(">>>Avec l'ip recu: %s:%s\n", new_user.get_ip(), new_user.get_port());
						new_user.set_socket(descripter_toread);

						while (m_participants.size() >= MAX_CONNECTIONS) {
							Participant p = getMaxP_Participants();
							std::cout << "Supprimer le participant " << p.get_port() << std::endl;
							FD_CLR(p.get_socket(), &m_descriptor_users);
							removeUser(p);
							closesocket(p.get_socket());
							m_participantMy.dec_NumP();
						}

						m_participants.push_back(new_user);
						m_participantMy.inc_NumP();

						//On informe les autres participants de la mise à jour la vue de serveur
						headerPDU head;
						head.type = 'C'; //Comme Changé
						head.len = (int)sizeof(Participant);
						for (Participant p : m_participants) {
							send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
							send_s(p.get_socket(), (char*)&m_participantMy, sizeof(m_participantMy), 0);
						}
						
						printf(">>Fin de lecture du header INFO ADD IP\n");
					}
					else if (head.type == 'C') {
						printf(">>Lecture du header Participant changé\n");
						printf(">>>Taille recu: %i\n", head.len);
						Participant user;
						recv_s(descripter_toread, (char*)(&user), sizeof(user), 0);
						user.set_socket(descripter_toread);
						for (int i = 0; i < m_participants.size(); i++) {
							if (user == m_participants[i]) {
								if (user.get_numP() != m_participants[i].get_numP()) {
									m_participants[i].set_numP(user.get_numP()); //mise à jour la vue
								}
							}
						}
						printf(">>Fin de lecture du header Participant changé\n");
					}
					else if (head.type == 'R') {
						printf(">>Lecture du header REQUESTER\n");
						headerPDU head;
						head.type = 'A'; //Comme Answer
						head.len = (int)m_allMessages.size() * (int)sizeof(Message);
						printf(">>>Taille envoye: %i\n", head.len);
						send_s(descripter_toread, (char*)&head, sizeof(head), 0);
						for (Message mes: m_allMessages) {
							send_s(descripter_toread, (char*)&mes, sizeof(Message), 0);
							send_s(descripter_toread, (char*)mes.get_content(), mes.get_size(), 0);
						}
					}
					else if (head.type == 'A') {
						printf(">>Lecture du header ANNOUNCE\n");
						printf(">>>Taille recu: %i\n", head.len);
						
						for (int i = 0; i < (head.len / (int)sizeof(Message)); i++) {
							Message mes;
							recv_s(descripter_toread, (char*)(&mes), sizeof(mes), 0);
							mes.set_content(malloc(mes.get_size()));
							recv_s(descripter_toread, (char*)mes.get_content(), mes.get_size(), 0);

							//Est-ce que le message est déjà dans liste des messages?
							if (m_allMessages.find(mes) == m_allMessages.end()) { // Vérification si le message existe déjà (Même m_uid)
								addMessage(mes); // On rajoute et envoie le nouveau message							
							}							
						}
						printf(">>Fin de lecture du header ANSWER\n");
					}
					else {
						printf("!!Lecture du header INCONNU!!!\n");
						exit(2);
					}
				}
				else {
					Participant p = getParticipantFromSocket(descripter_toread);
					FD_CLR(descripter_toread, &m_descriptor_users);
					removeUser(p);
					closesocket(descripter_toread);
					printf("(Connection close by client %s)\n", p.get_name());
					
					// Envoie une annonce de déconnexion du client p
					addMessage(Message('d', p, (void*)"", 1));

					m_participantMy.dec_NumP();

					//on informe les autres participants d'un participant qui vient de quitter
					headerPDU head;
					head.type = 'C'; //Comme Changé
					head.len = (int)sizeof(Participant);
					for (Participant p : m_participants) {
						send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
						send_s(p.get_socket(), (char*)&m_participantMy, sizeof(m_participantMy), 0);
					}
				}
			}

		}
		fd_users_to_read = m_descriptor_users;
	}
	perror("Select error");
	exit(EXIT_FAILURE);
}

void Discussion::requestInfoParticipant(Participant p) {
	headerPDU head;
	head.type = 'J'; //Comme I+1
	head.len = (int)sizeof(Participant);
	send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
	printf(">>> Request IPs LIST to invite socket\n");
	send_s(p.get_socket(), (char*)&m_participantMy, sizeof(Participant), 0);
}

void Discussion::requestMessagesParticipant(Participant p) {
	headerPDU head;
	head.type = 'R'; //Comme REQUEST
	printf(">>> Request MESSAGES to invite socket\n");
	send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
}

void Discussion::infoParticipant(Participant p) {
	headerPDU head;
	head.type = 'F'; //Comme inFo
	head.len = (int)sizeof(Participant);
	send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
	send_s(p.get_socket(), (char*)&m_participantMy, sizeof(Participant), 0);
}

void Discussion::sendMParticipants(Participant p) {
	headerPDU head;
	head.type = 'I'; //Comme IP
	head.len = ((int)m_participants.size() - 1) * (int)sizeof(Participant); // -1 Car une des IP sera bloqué par la condition addr.socket!=sock \_
	send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
	send_s(p.get_socket(), m_discussion_title, TITLE_LENGTH, 0);

	for (Participant addr : m_participants) {
		printf(">>>>Envoie de l'ip: %s:%s:%lli", addr.get_ip(), addr.get_port(), addr.get_socket());
		if (addr.get_socket() != p.get_socket()) {
			send_s(p.get_socket(), (char*)&addr, sizeof(addr), 0);
		}
		else {
			printf(" (Cette IP est celle recu! Pas d'envoie)");
		}
		printf("\n");
	}

	//on envoie la vue de serveur
	head.type = 'C'; //Comme IP
	head.len = (int)sizeof(Participant);
	send_s(p.get_socket(), (char*)&head, sizeof(head), 0);
	send_s(p.get_socket(), (char*)&m_participantMy, sizeof(m_participantMy), 0);
}

Participant Discussion::addUser(Participant p) {

	//--------------- Ce code est largement inspiré de la doc Microsoft (Vu également en TD) ---------------
	// Connexion vers un client: https://docs.microsoft.com/en-us/windows/win32/winsock/complete-client-code
	struct addrinfo* resultfor = NULL, * ptr = NULL, hints;
	ZeroMemory(&hints, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_protocol = IPPROTO_TCP;

	int iResult;
	// Réccupération des méthodes de connexion pour le client
	printf(">> Resolution de la connexion avec %s:%s\n", p.get_ip(), p.get_port());
	iResult = getaddrinfo(p.get_ip(), p.get_port(), &hints, &resultfor);
	if (iResult != 0) {
		printf("!! getaddrinfo failed with error: %d\n", iResult);
		WSACleanup();
		system("pause");
		exit(1);
	}

	// Chaque méthode de connexion est testé jusqu'à une qui fonctionne
	for (ptr = resultfor; ptr != NULL; ptr = ptr->ai_next) {
		// Create a SOCKET for connecting to server
		p.set_socket(socket(ptr->ai_family, ptr->ai_socktype,
			ptr->ai_protocol));
		if (p.get_socket() == INVALID_SOCKET) {
			printf("!! Socket failed with error: %ld\n", WSAGetLastError());
			WSACleanup();
			system("pause");
			exit(1);
		}

		// Connect to server.
		iResult = connect(p.get_socket(), ptr->ai_addr, (int)ptr->ai_addrlen);
		if (iResult == SOCKET_ERROR) {
			closesocket(p.get_socket());
			p.set_socket(INVALID_SOCKET);
			continue;
		}
		break;
	}

	if (p.get_socket() == INVALID_SOCKET) {
		printf("!! Unable to connect to server!\n");
		WSACleanup();
		Participant p;
		return p;
		//system("pause");*/
		//exit(1);
	}
	//--------------------------
	// La connexion à réussi !
	printf(">> Connexion reussi par cle d'invitation\n");

	Participant tmp_ip = getParticipantFromSocket(p.get_socket());
	m_participantMy.set_ip(tmp_ip.get_ip()); //On définie l'ip d'invitation de my Participation

	addIP(p);

	return p;
}

void Discussion::addIP(Participant container) {
	m_participantMy.inc_NumP();
	//std::cout << "Nombre de Participant de serveur is " << m_participantMy.get_numP() << std::endl;
	container.inc_NumP(); //incrémente 1 car container connecte à serveur
	std::cout << "Vue de participant " << container.get_port() << " is " << container.get_numP() << std::endl;
	m_participants.push_back(container);
	FD_SET(container.get_socket(), &m_descriptor_users); //On ajoute le participant à la conversation
}

void Discussion::addMessage(Message message) {
	sendMessage(message); // Envoie le nouveau message à tous les peers
	m_allMessages.insert(message); // Rajoute le message dans notre liste de message

	if (message.get_type() == 'n' && parentOwnerOf(message)) { //New message announce et je suis le propriétaire
		if (message.get_creator() == m_participantMy || getMessage(Message(((messageStruct*)(message.get_content()))->parent)).locked == false)
			addMessageOwnerConfirmation(message);
	}

	if (message.get_type() == 'f' && ownerOf( Message( ((messageEditStruct*)(message.get_content()))->uid ) )){ //New edit announce et je suis le propriétaire
		if(message.get_creator() == m_participantMy || getMessage(Message(((messageEditStruct*)(message.get_content()))->uid)).locked == false)
			editMessageOwnerConfirmation(message);
	}

	if (message.get_type() == 'e') {
		std::set<Message>::iterator it = m_allMessages.find(Message(((messageEditStruct*)(message.get_content()))->uid));
		Message find = *it;
		find.set_creator(((messageEditStruct*)(message.get_content()))->creator);
		find.set_date_char(((messageEditStruct*)(message.get_content()))->char_date);
		memcpy_s(find.get_content(), find.get_size(), &(((messageEditStruct*)(message.get_content()))->message), sizeof(messageStruct));

		m_allMessages.erase(it);
		m_allMessages.insert(find);
	}

	if (message.get_type() == 'k' && ownerOf(Message(((messageLockStruct*)(message.get_content()))->uid))) { //New lock announce et je suis le propriétaire
		if (message.get_creator() != m_participantMy && getMessage(Message(((messageLockStruct*)(message.get_content()))->uid)).locked == false) {
			//Si le message ne vient pas du propriétaire et que le message n'est pas lock, on change le propriétaire
			//Nous ne sommes plus propriétaire
			printf("Abandon de propriete\n");
			std::set<Message>::iterator it = m_allMessages.find( Message(((messageLockStruct*)(message.get_content()))->uid) );
			Message find = *it;
			find.set_owner(message.get_creator());

			m_allMessages.erase(it);
			m_allMessages.insert(find);
		}

		if (message.get_creator() == m_participantMy || getMessage(Message(((messageLockStruct*)(message.get_content()))->uid)).locked == false) {
			//Si la demande vient de moi même ou que le message n'est pas lock et vient de quelqu'un d'autre
			//On transmet un message de lock
			lockMessageOwnerConfirmation(message);
		}
	}

	if (message.get_type() == 'l') {
		std::set<Message>::iterator it = m_allMessages.find( Message(((messageLockStruct*)(message.get_content()))->uid) );
		Message find = *it;
		//Le participant devient le propriétaire du message
		find.set_owner(message.get_creator());
		//On modifie le lock du Message
		find.locked = ((messageLockStruct*)(message.get_content()))->locked;

		m_allMessages.erase(it);
		m_allMessages.insert(find);		
	}

	if (message.get_type() == 'd') {
		// Déconnexion d'un propriétaire
		Participant dead = message.get_creator();
		std::cout << "Examining lost owner's messages\n";
		std::cout << "Lost owner is " << dead.get_ip() << ":" << dead.get_port() << std::endl;

		std::vector<Message> ownerToSetToNull;
		for (Message m : m_allMessages)
		{
			std::cout << "Comparing to owner " << m.get_owner().get_ip() << ":" << m.get_owner().get_port() << std::endl;
			if (m.get_owner() == dead) {
				ownerToSetToNull.push_back(m);
				std::cout << "Dead message discovered !";
			}
		}
		for (Message m : ownerToSetToNull) {
			std::set<Message>::iterator it = m_allMessages.find(m);
			Message find = *it;
			find.set_owner(PARTICIPANT_NULL);
			m_allMessages.erase(it);
			m_allMessages.insert(find);
		}
	}

	changes++;
}

void Discussion::lockMessageOwnerConfirmation(Message message) {
	Message new_mes('l', message.get_creator(), malloc(message.get_size()), message.get_size()); // On créer un nouveau message
	memcpy_s(new_mes.get_content(), new_mes.get_size(), message.get_content(), message.get_size()); // Qui est une copie du message du base, avec seulement 'k'>'l' de modifié

	addMessage(new_mes); //On envoie la modification
}

void Discussion::editMessageOwnerConfirmation(Message message) {
	Message new_mes('e', message.get_creator(), malloc(message.get_size()), message.get_size()); // On créer un nouveau message
	memcpy_s(new_mes.get_content(), new_mes.get_size(), message.get_content(), message.get_size()); // Qui est une copie du message du base, avec seulement 'f'>'e' de modifié

	addMessage(new_mes); //On envoie la modification
}

void Discussion::addMessageOwnerConfirmation(Message message) {
	Message new_mes('m', message.get_creator(), malloc(message.get_size()), message.get_size()); // On créer un nouveau message
	memcpy_s(new_mes.get_content(), new_mes.get_size(), message.get_content(), message.get_size()); // Qui est une copie du message du base, avec seulement 'n'>'m' de modifié

	addMessageAsOwner(new_mes); //On envoie le message ajouté
}

void Discussion::addMessageAsOwner(Message message) {
	message.set_owner(get_participantMy());
	addMessage(message);
}

void Discussion::sendMessage(Message message) {
	for (u_int i = 0; i < m_descriptor_users.fd_count; i++) { //On envoie à tous les clients connu
		SOCKET descripter_tosend = m_descriptor_users.fd_array[i];
		if (descripter_tosend != m_participantMy.get_socket()) {
			headerPDU head;
			head.type = 'A'; //Comme Answer
			head.len = (int)sizeof(Message); //On envoie 1 message
			printf("---Envoie d'un message de taille: %i\n", head.len);
			send_s(descripter_tosend, (char*)&head, sizeof(head), 0);
			send_s(descripter_tosend, (char*)&message, sizeof(Message), 0);
			send_s(descripter_tosend, (char*)message.get_content(), message.get_size(), 0);
		}
	}
}

std::set<Message> Discussion::getAllDiscussion()
{
	//std::vector<Message> allMessages; 
	//for (Message mes : m_allMessages) { //On rajoute chaque Message dans la liste à transmettre
	//	if (std::find(allMessages.begin(), allMessages.end(), mes) == allMessages.end()) { // Vérification si le message existe déjà (Même m_uid)
	//		allMessages.push_back(mes); //On fournit pas les messages étant déjà dans la liste, >donc ayant eu des modifications<
	//	}
	//}
	return m_allMessages;
}

void Discussion::removeUser(Participant p)
{
	int i = 0;
	printf(">> removeUser : liste des sockets: (Avec %s a supprimer)\n>>           ", p.get_name());
	for (Participant ipToRemove : m_participants) {
		printf("-sockets: %lli-", ipToRemove.get_socket());
	}
	printf("\n");
	for (Participant ipToRemove : m_participants) {
		if (ipToRemove.get_socket() == p.get_socket()) {
			break;
		}
		i++;
	}
	m_participants.erase(m_participants.begin() + i);
}

void Discussion::stopDiscussion()
{
	if (!stopping) { //Si la boucle select et le thread "SELECT" existe
		stopping = true;
		m_listenThread.join(); //On s'assure que le thread "SELECT" est bien fermé
	}
}

Participant Discussion::get_participantMy()
{
	return m_participantMy;
}

void Discussion::set_participantMy(Participant p)
{
	m_participantMy = p;
}

void Discussion::set_participantMyName(char name[NAME_LENGTH])
{
	m_participantMy.set_name(name);
}

void Discussion::set_participantMyIP(char ip[IP_LENGTH]) {
	m_participantMy.set_ip(ip);
}

char* Discussion::get_title()
{
	return m_discussion_title;
}

void Discussion::setUserInterfacesIPs() {
	//--------------- Ce code est inspiré de la doc Microsoft ---------------
	// Récupère les informations sur l'adaptateur: https://docs.microsoft.com/en-us/windows/win32/api/iptypes/ns-iptypes-ip_adapter_info

	// It is possible for an adapter to have multiple
	// IPv4 addresses, gateways, and secondary WINS servers
	// assigned to the adapter. 
	//
	// Note that this sample code only prints out the 
	// first entry for the IP address/mask, and gateway, and
	// the primary and secondary WINS server for each adapter. 

	PIP_ADAPTER_INFO pAdapterInfo;
	PIP_ADAPTER_INFO pAdapter = NULL;
	DWORD dwRetVal = 0;

	ULONG ulOutBufLen = sizeof(IP_ADAPTER_INFO);
	pAdapterInfo = (IP_ADAPTER_INFO*)MALLOC(sizeof(IP_ADAPTER_INFO));
	if (pAdapterInfo == NULL) {
		printf("Error allocating memory needed to call GetAdaptersinfo\n");
		return;
	}

	// Make an initial call to GetAdaptersInfo to get
	// the necessary size into the ulOutBufLen variable
	if (GetAdaptersInfo(pAdapterInfo, &ulOutBufLen) == ERROR_BUFFER_OVERFLOW) {
		FREE(pAdapterInfo);
		pAdapterInfo = (IP_ADAPTER_INFO*)MALLOC(ulOutBufLen);
		if (pAdapterInfo == NULL) {
			printf("Error allocating memory needed to call GetAdaptersinfo\n");
			return;
		}
	}

	if ((dwRetVal = GetAdaptersInfo(pAdapterInfo, &ulOutBufLen)) == NO_ERROR) {
		pAdapter = pAdapterInfo;
		while (pAdapter) {
			printf("\tIP Address: \t%s\n",
				pAdapter->IpAddressList.IpAddress.String);
			if (strstr(pAdapter->Description, "VMware") == NULL) {
				if (strstr(pAdapter->IpAddressList.IpAddress.String, "0.0.0.0") == NULL) {
					printf("\tIP Address: \t%s\n",
						pAdapter->IpAddressList.IpAddress.String);
					m_list_interface_ip.push_back(pAdapter->IpAddressList.IpAddress.String);
				}
			}	
			pAdapter = pAdapter->Next;
		}
	}
	else {
		printf("GetAdaptersInfo failed with error: %d\n", dwRetVal);

	}
	if (pAdapterInfo)
		FREE(pAdapterInfo);

	std::string localhost = "127.0.0.1";
	m_list_interface_ip.push_back(localhost);
}

std::vector<std::string> Discussion::getLocalIPs() {
	return m_list_interface_ip;
}

bool Discussion::parentOwnerOf(Message message) {
	if (message.get_type() != 'n') {
		exit(-1);
	}
	
	Message to_search = Message(((messageStruct*)message.get_content())->parent);
	return ownerOf(to_search);
}

bool Discussion::ownerOf(Message message) {
	std::set<Message>::iterator it = m_allMessages.find(message);
	if (it != m_allMessages.end()) {
		Message find = *it;
		return find.get_owner() == m_participantMy;
	}
	else {
		//Si on est ici, ce n'est pas normal cela veut dire que l'on recherche un message qui n'existe pas
		printf("ERROR");
		exit(3);
	}
}

bool Discussion::hasChanged()
{
	return changes!=0;
}

void Discussion::lessChanges()
{
	changes--;
}

bool Discussion::isStopping()
{
	return stopping;
}

Message Discussion::getMessage(Message message) {
	std::set<Message>::iterator it = m_allMessages.find(message);
	return *it;
}

char* Discussion::get_id() {
	return m_id;
};