cmake_minimum_required(VERSION 3.10)
project(models LANGUAGES C CXX)
add_subdirectory(rootsim_core)


add_executable(phold phold/application.c phold/functions.c)
target_link_libraries(phold PRIVATE rscore)
target_include_directories(phold PRIVATE rootsim_core/src)
target_include_directories(phold PRIVATE .)

add_executable(tbc tbc/application.c tbc/guy.c tbc/guy_init.c tbc/parameters.c)
target_link_libraries(tbc PRIVATE rscore)
target_include_directories(tbc PRIVATE rootsim_core/src)
target_include_directories(tbc PRIVATE .)