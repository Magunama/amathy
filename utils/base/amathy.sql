create database animevibe;

create schema amathy;

create table if not exists amathy.coins
(
    user_id numeric(18)       not null
        constraint coins_pk
            primary key,
    pocket  integer default 0 not null,
    bank    integer default 0 not null
);

create table if not exists amathy.definitions
(
    id            serial      not null
        constraint definitions_pk
            primary key,
    def_name      text        not null,
    def_body      text        not null,
    def_guild_id  numeric(18) not null,
    def_author_id numeric(18) not null,
    def_time      timestamp   not null,
    def_global    boolean     not null
);

create index if not exists definitions_def_author_id_index
    on amathy.definitions (def_author_id);

create index if not exists definitions_def_guild_id_index
    on amathy.definitions (def_guild_id);

create index if not exists definitions_def_name_index
    on amathy.definitions (def_name);

create unique index if not exists definitions_def_name_uindex
    on amathy.definitions (def_name);

create unique index if not exists definitions_id_uindex
    on amathy.definitions (id);

create table if not exists amathy.disabled_events
(
    guild_id numeric(18)                 not null
        constraint table_name_pk
            primary key,
    key_drop text[] default '{}'::text[] not null
);

create unique index if not exists table_name_guild_id_uindex
    on amathy.disabled_events (guild_id);

create table if not exists amathy.hentai
(
    id   serial not null
        constraint hentai_pk
            primary key,
    link text   not null
);

create table if not exists amathy.stats
(
    user_id   numeric(18)                not null
        constraint stats_pk
            primary key,
    xp        integer default 0          not null,
    gems      integer default 0          not null,
    vip_days  integer default 0          not null,
    inventory json    default '{}'::json not null
);

create table if not exists amathy.timers
(
    user_id  numeric(18)                                                          not null
        constraint timers_pk
            primary key,
    daily    timestamp default '0001-01-01 00:00:00'::timestamp without time zone not null,
    bet      timestamp default '0001-01-01 00:00:00'::timestamp without time zone not null,
    bet_left integer   default 20                                                 not null,
    wheel    timestamp default '0001-01-01 00:00:00'::timestamp without time zone not null
);

create table if not exists amathy.votes
(
    user_id       numeric(18)                                                          not null
        constraint votes_pk
            primary key,
    monthly_votes integer   default 0                                                  not null,
    last_vote     timestamp default '0001-01-01 00:00:00'::timestamp without time zone not null,
    total_votes   integer   default 0                                                  not null
);


