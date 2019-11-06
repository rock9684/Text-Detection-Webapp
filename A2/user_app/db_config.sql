-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET SQL_SAFE_UPDATES = 0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema ece1779_hw
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ece1779_hw` DEFAULT CHARACTER SET latin1 ;
USE `ece1779_hw`;

-- -----------------------------------------------------
-- Table `ece1779_hw`.`users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_hw`.`users`;

CREATE TABLE IF NOT EXISTS `ece1779_hw`.`users` (
  `userid` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `salt` TEXT NOT NULL,
  `hhash` TEXT NOT NULL,
  `count` INT NOT NULL,
  PRIMARY KEY (`userid`)
)
DEFAULT CHARACTER SET = latin1;

-- -----------------------------------------------------
-- Table `ece1779_hw`.`images`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_hw`.`images` ;

CREATE TABLE IF NOT EXISTS `ece1779_hw`.`images` (
  `imid` INT NOT NULL AUTO_INCREMENT,
  `userid` INT NOT NULL,
  `namebase` TEXT NOT NULL,
  `extension` TEXT NOT NULL,
  PRIMARY KEY (`imid`),
  FOREIGN KEY (`userid`) REFERENCES users(`userid`)
)
DEFAULT CHARACTER SET = latin1;

CREATE USER 'ece1779_hw' IDENTIFIED BY 'ece1779_hw_pass';
commit;

GRANT ALL ON ece1779_hw.* TO 'ece1779_hw';


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

