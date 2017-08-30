BEGIN TRANSACTION;
CREATE TABLE "user" (
	`id`	INTEGER NOT NULL,
	`username`	VARCHAR(32),
	`password_hash`	VARCHAR(64),
	`name`	VARCHAR(250),
	`email`	VARCHAR(250),
	`picture`	VARCHAR(250),
	`token`	TEXT,
	PRIMARY KEY(`id`)
);
INSERT INTO `user` VALUES (1,NULL,NULL,'kodie ivie','kodieivie@gmail.com','https://lh6.googleusercontent.com/-y358BbEW440/AAAAAAAAAAI/AAAAAAAAiEg/Q3xAfosaKdo/photo.jpg',NULL);
INSERT INTO `user` VALUES (2,'world','$6$rounds=656000$Q1SdFxvp7NnEvcZt$9L4h1gaux5dbhWbn3ClI.8L55gn73ubslB/.qyLntjdwexh5eC40DBH/mhxkmzmAQY14aw.eZ4el8ds28D7Fv1',NULL,NULL,NULL,NULL);
INSERT INTO `user` VALUES (3,NULL,NULL,'Kodie Ivie2','kodieivie2@gmail.com','https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg',NULL);
CREATE TABLE category (
	id INTEGER NOT NULL, 
	name VARCHAR(250) NOT NULL, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO `category` VALUES (1,'Programming Languages',1);
INSERT INTO `category` VALUES (2,'Movies',1);
INSERT INTO `category` VALUES (3,'Sports',1);
INSERT INTO `category` VALUES (4,'Marine life',1);
INSERT INTO `category` VALUES (5,'animals at the zoo',1);
INSERT INTO `category` VALUES (6,'planets',1);
CREATE TABLE catalogitem (
	name VARCHAR(80) NOT NULL, 
	id INTEGER NOT NULL, 
	description VARCHAR(250), 
	category_id INTEGER, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES category (id), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO `catalogitem` VALUES ('python',1,'not a snake',1,1);
INSERT INTO `catalogitem` VALUES ('ajax',2,'xml''s replacement',1,1);
INSERT INTO `catalogitem` VALUES ('good movie',3,'its a great movie',2,1);
INSERT INTO `catalogitem` VALUES ('comic',4,'so funny',2,1);
INSERT INTO `catalogitem` VALUES ('Basketball',5,'Great game',3,1);
INSERT INTO `catalogitem` VALUES ('baseball',6,'fun to play but boring to watch',3,1);
INSERT INTO `catalogitem` VALUES ('sumo wrestling',7,'do they still do this?',3,1);
INSERT INTO `catalogitem` VALUES ('octopus',8,'Something i would love as a pet!',4,1);
INSERT INTO `catalogitem` VALUES ('puffer fish',9,'I had two of these but they couldn''t get along.',4,1);
INSERT INTO `catalogitem` VALUES ('lion',10,'king baby!',5,1);
INSERT INTO `catalogitem` VALUES ('zebra',11,'Lion food',5,1);
INSERT INTO `catalogitem` VALUES ('giraffe',12,'such an odd creature',5,1);
INSERT INTO `catalogitem` VALUES ('Earth',13,'A place where aliens dropped off their experiments.',6,1);
INSERT INTO `catalogitem` VALUES ('moon',14,'earths cozy planet, people used to worship it.',6,1);
CREATE INDEX ix_user_username ON user (username)



;
COMMIT;
