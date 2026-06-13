# terraform/vpc.tf

# ─────────────────────────────────────────
# VPC — Your private network on AWS
# ─────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# INTERNET GATEWAY
# Connects VPC to the internet
# Without this, nothing in VPC can reach internet
# ─────────────────────────────────────────

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "${var.project_name}-igw"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# PUBLIC SUBNET
# EC2 lives here
# map_public_ip_on_launch = EC2 gets public IP automatically
# ─────────────────────────────────────────

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name    = "${var.project_name}-public-subnet"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# PRIVATE SUBNET 1
# RDS lives here — no direct internet access
# ─────────────────────────────────────────

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = "${var.aws_region}a"

  tags = {
    Name    = "${var.project_name}-private-subnet-1"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# PRIVATE SUBNET 2
# RDS requires subnets in 2 availability zones
# ─────────────────────────────────────────

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr_2
  availability_zone = "${var.aws_region}b"

  tags = {
    Name    = "${var.project_name}-private-subnet-2"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# PUBLIC ROUTE TABLE
# Rules: local traffic stays inside VPC
#        everything else goes to internet via IGW
# ─────────────────────────────────────────

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name    = "${var.project_name}-public-rt"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# ASSOCIATE PUBLIC SUBNET WITH PUBLIC ROUTE TABLE
# Without this, subnet doesn't use the route table
# ─────────────────────────────────────────

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ─────────────────────────────────────────
# PRIVATE ROUTE TABLE
# Only local traffic — no internet access
# RDS should never talk to internet directly
# ─────────────────────────────────────────

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "${var.project_name}-private-rt"
    Project = var.project_name
  }
}

# Associate both private subnets with private route table
resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}

# ─────────────────────────────────────────
# DB SUBNET GROUP
# Tells RDS which subnets it can use
# Must span 2 availability zones
# ─────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name    = "${var.project_name}-db-subnet-group"
    Project = var.project_name
  }
}