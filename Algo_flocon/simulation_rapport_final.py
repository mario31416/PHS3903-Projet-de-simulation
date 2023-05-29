from hexalattice.hexalattice import *
import numpy as np
from fonctions_frontieres import *
from fonctions_plot import * 
import time 
from numpy import ndenumerate
from memory_profiler import profile

# ----------TIME----------------
start = time.time()

# ---------PARAMETRES--------------------

# rho = 0.58    # Densite
# kappa = 0.1   # Freezing parameter
# iterations = 10 # Number of iterations  A UTILISER !
# alpha = 0.08
# beta = 2
# theta = 0.011
# mu = 0.01
# gamma = 0.0005

# rho = 0.1     # Densite
# kappa = 0.001  # Freezing parameter
# iterations = 100 # Number of iterations  A UTILISER !
# alpha = 0.35
# beta = 1.06
# theta = 0.112
# mu = 0.14
# gamma = 0.00006

rho = 0.635    # Densite
kappa = 0.0075  # Freezing parameter
iterations = 2000 # Number of iterations  A UTILISER !
alpha = 0.4
beta = 1.6
theta = 0.025
mu = 0.015
gamma = 0.0005
filepath = '/Users/marielafontaine/Documents/GitHub/PHS3903-Projet-de-simulation/Figures_rapportfinal'


#rho_values = [0.16, 0.38, 0.77, 0.95]
# alpha_values = [0.001, 0.4, 0.08, 0.6]
# # theta_values = [0.015, 0.1, 0.025, 0.067]
# mu_values = [0, 0.015, 0.07, 0.1]
# gamma_values = [0, 0.0001, 0.0005, 0.01]
#kappa_values = [0.001, 0.05, 0.1, 0.2]
beta_values = [2.2]






# ----------RESEAU -------------------
N =300 # Taille de la grille 
hex_centers, _ = create_hex_grid(nx=N,          # Création du résau 
                                ny=N,
                                do_plot=False)
                                
x_hex_coords = hex_centers[:, 0]
y_hex_coords = hex_centers[:, 1]

color_vapor = np.full((N ** 2,3), [1,0, 0]) # ROUGE pour la vapeur 
color_ice = np.full((N ** 2,3), [0, 0, 1]) # BLEU pour la glace 
color_quasi = np.full((N ** 2,3), [0, 1, 0]) # VERT pour quasi-liquid 

colors_init = color_ice + color_vapor + color_quasi 

# --------------------------- MASK INITIAL --------------------
for k in range(len(beta_values)) :
    beta = beta_values[k]
    mask_tot = np.full((N ** 2,4), [0, 0, 0, rho])    # Mask totale a=(0 ou 1 si dans cristal) b : boundary mass (quasi-liquid)
                                        # c : cristal mass (ice) d : diffusive mass (vapor)

    if N%2 == 0 : # donc pair !
        mask_tot[int((len(mask_tot) / 2)-N/2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
        cell_centre_domaine = int((len(mask_tot) / 2) - N/2)
    else:
        mask_tot[int(len(mask_tot) / 2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
        cell_centre_domaine = int((len(mask_tot) / 2))

# Cristal initial en triangle
# mask_tot[int((len(mask_tot) / 2)-N/2)+N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+2*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N-2] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N+1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-2] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-1] = [1, 0, 1, 0]

# Cristal initial en Y
# mask_tot[int((len(mask_tot) / 2)-N/2)+3*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+2*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-3*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-2*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+3] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+2] = [1, 0, 1, 0]


# ----------------------FONCTIONS ÉVOLUTION---------------------------


    _range_mask_tot = len(mask_tot)
    def freezing(mask0, N, centre, kappa) :
        ## b0, d0 = masques initiaux 
        # centre = index
        mask1 = mask0
        idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


        idx = [idxb,idxc,idxd,idxe,idxf,idxg]
        for i in range(len(idx)) :
            mask1[idx[i],1] = mask0[idx[i], 1] + ((1-kappa)*mask0[idx[i], 3])

            mask1[idx[i],2]= mask0[idx[i], 1] + (kappa*mask0[idx[i], 3])

            mask1[idx[i],3] = 0

        return mask1

    def melting(mask0, N, centre, mu, gamma) :
        ## b0, d0 = masques initiaux 
        # centre = index
        mask1 = mask0
        idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


        idx = [idxb,idxc,idxd,idxe,idxf,idxg]
        for i in range(len(idx)) :
            mask1[idx[i],1] = (1-mu)*mask0[idx[i],1]

            mask1[idx[i],2]= (1-gamma)*mask0[idx[i],2]

            mask1[idx[i],3] = mask0[idx[i],3] + mu*mask0[idx[i],1] + gamma*mask0[idx[i],2]

        return mask1

    def attachement(mask0, N, centre, alpha, beta, theta):
        # ne fonctionne pas sur les frontières !
        if centre%N == 0 or (centre+1)%N == 0 or centre < N or centre > N*(N-1): # les frontières sont exclues
            return mask0 # Rien ne change


        nb_voisin_cristal = prox_crystal(mask0,centre)  # Entier qui donne le nb de voisin gelé
        idx_voisins = alentours_idx(N,centre)[1:]       # idx des voisins du centre, excluant idx centre

        vapeur_voisin_liste = [mask0[ele, 3] for ele in idx_voisins] # List comprehension 

        val_somme_vapeur_voisin = sum(vapeur_voisin_liste) # la somme de la vapeur des voisin du centre

        mask1 = mask0 #initialisation
        
        if nb_voisin_cristal != 0 and mask0[centre,0] == 0 :
            #1 cas nb = 1 ou 2
            if nb_voisin_cristal == 1 or 2 :
                
                if mask0[centre,1] >= beta:
                    mask1[centre,0] = 1
                    mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                    mask1[centre,1] = 0

            #2 cas nb = 3
            if nb_voisin_cristal == 3 :
                
                if mask0[centre,1] >= 1 or (val_somme_vapeur_voisin < theta and mask0[centre,1] > alpha):
                #if mask0[centre,1] >= 1:
                    mask1[centre,0] = 1
                    mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                    mask1[centre,1] = 0
            #3 cas nb >= 4
            if nb_voisin_cristal >= 4 :
                
                mask1[centre,0] = 1
                mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                mask1[centre,1] = 0
        return mask1


    #print(type(mask_tot))
    # -----------------------UDPDATE MASK ------------------------------




    for t in range(iterations):
    #           FREEZING
        a = np.where(mask_tot[:,0]==1)
        for ele in a[0] :
            mask_change = freezing(mask_tot, N, ele, kappa)
        mask_tot = mask_change

    #           MELTING
        a = np.where(mask_tot[:,0]==1)
        for ele in a[0] :
            mask_change = melting(mask_tot, N, ele, mu, gamma)
        mask_tot = mask_change


        #plot_total(mask_tot, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)

        for i in range(_range_mask_tot):
            #                   ATTACHEMENT
            #print(i,'>>>',type(i),'>>>>>>')
            mask_change = attachement(mask_tot, N, i, alpha, beta, theta)
        #plot_total(mask_change, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)

            #                  DIFFUSION
        
        mask_1 = np.copy(mask_change)

        for i in range(_range_mask_tot):
            
            if i%N == 0 or (i+1)%N == 0 or i < N or i > N*(N-1):    
                continue   

            elif mask_1[i,0]==1:
                continue

            elif prox_crystal(mask_1,i) != 0: # est a proximité du cristal, condition réfléchie
                mask_change[i,3] = somme_vap_voisin_cristal(mask_1, i, N) #Laplacien condition réfléchie

            else:  
                ele = alentours(mask_1,i) #
                mask_change[i,3] = somme_vap(ele) 
        
        mask_tot = mask_change
        print(t)


    # if __name__ == '__main__':
    #     my_func()

    end = time.time()
    print(f"Runtime of the program is {end - start}")


    # ---------------------PLOT RESULTS------------------------------------


    # GLACE 
    ice = mask_tot[:,0]
    final_mask_ice = []
    for i in range(len(mask_tot)):
        for j in range(3):
            final_mask_ice.append(ice[i])

    final_mask_ice_reshaped = np.reshape(final_mask_ice, (N**2, 3))
    final_color_ice = (color_ice * final_mask_ice_reshaped) 
    # VAPEUR
    vapor = mask_tot[:,3]
    final_mask_vapor = []
    for i in range(len(mask_tot)):
        for j in range(3):
            final_mask_vapor.append(vapor[i])

    final_mask_vapor_reshaped = np.reshape(final_mask_vapor, (N**2, 3))
    final_color_vapor = (color_vapor * final_mask_vapor_reshaped) 


    # QUASI-LIQUIDE
    quasi_liquid = mask_tot[:,1]
    final_mask_quasi_liquid = []
    for i in range(len(mask_tot)):
        for j in range(3):
            final_mask_quasi_liquid.append(quasi_liquid[i])

    final_mask_quasi_liquid_reshaped = np.reshape(final_mask_quasi_liquid, (N**2, 3))
    final_color_quasi_liquid = (color_quasi * final_mask_quasi_liquid_reshaped) 



    final_colors = final_color_ice + final_color_vapor + final_color_quasi_liquid



    max = np.max(final_colors)
    final_colors = final_colors/max

    max = np.max(final_color_ice)
    final_color_ice = final_color_ice/max

    max = np.max(final_color_vapor)
    final_color_vapor = final_color_vapor/max

    max = np.max(final_color_quasi_liquid)
    final_color_quasi_liquid = final_color_quasi_liquid/max


    plt.figure(1)
    plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       # Plot total des 3 phases 
                                        face_color= final_colors,
                                        edge_color=final_colors,
                                        min_diam=1,
                                        plotting_gap=0.0,
                                        rotate_deg=0)
    plt.title('Mask total')
    plt.axis('off')
    plt.savefig(f'{filepath}/Sim4_{k}_Masktot', dpi = 500)

    plt.figure(2)

    plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                        face_color= final_color_ice,
                                        edge_color=final_color_ice,
                                        min_diam=1,
                                        plotting_gap=0.0,
                                        rotate_deg=0)
    plt.title('Mask glace')
    plt.axis('off')
    plt.savefig(f'{filepath}/Sim4_{k}_glace', dpi = 500)

    plt.figure(3)

    plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                        face_color=final_color_vapor,
                                        edge_color=final_color_vapor,
                                        min_diam=1,
                                        plotting_gap=0.0,
                                        rotate_deg=0)

    plt.title('Mask vapeur')
    plt.axis('off')
    plt.savefig(f'{filepath}/Sim4_{k}_vapeur', dpi = 500)

    plt.figure(k)
    

    plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                        face_color=final_color_quasi_liquid,
                                        edge_color=final_color_quasi_liquid,
                                        min_diam=1,
                                        plotting_gap=0.0,
                                        rotate_deg=0)

    plt.title(f'Mask quasi liquid beta = {beta}')
    plt.axis('off')
    plt.savefig(f'{filepath}/Sim4_{k}_QLL', dpi = 500)
